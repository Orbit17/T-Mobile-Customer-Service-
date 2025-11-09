from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Tuple
import os
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
import requests
from dotenv import load_dotenv

from .models import Event, Alert, Runbook, CHI

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def _collect_context(db: Session, lookback_hours: int = 24) -> List[Tuple[str, str]]:
    """
    Returns list of (type, text) items to feed into retrieval.
    """
    now = datetime.utcnow()
    start = now - timedelta(hours=lookback_hours)
    docs: List[Tuple[str, str]] = []
    # Recent alerts
    alerts = list(
        db.scalars(select(Alert).where(Alert.ts >= start).order_by(desc(Alert.ts)))
    )
    for a in alerts:
        docs.append(("alert", f"[{a.region}] {a.reason} | recs: {', '.join(a.recommendation or [])}"))
    # Recent events (sample strongest negative/positive)
    events = list(
        db.scalars(
            select(Event)
            .where(Event.ts >= start)
            .order_by(desc(Event.ts))
            .limit(500)
        )
    )
    for e in events:
        docs.append(("event", f"[{e.region}] sent={e.sentiment:.2f} topic={e.topic or 'other'} text={e.text[:240]}"))
    # Runbook
    runbooks = list(db.scalars(select(Runbook)))
    for r in runbooks:
        docs.append(("runbook", f"Runbook for {r.issue}: steps={'; '.join(r.steps)}"))
    # Latest CHI per region
    regions = sorted({e.region for e in events})
    for region in regions:
        row = db.scalars(
            select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(1)
        ).first()
        if row:
            drivers = row.drivers_json or {}
            docs.append(("chi", f"[{region}] CHI={row.score:.1f} sentiment={drivers.get('sentiment', 0):.2f} "
                                 f"kpi={drivers.get('kpi_health', 0):.2f} top={', '.join(drivers.get('top_keywords', [])[:5])}"))
    return docs


def answer_question(db: Session, question: str) -> dict:
    docs = _collect_context(db)
    corpus = [d[1] for d in docs]
    if not corpus:
        return {"summary": "No data available.", "drivers": {}, "actions": []}
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus + [question])
    sims = cosine_similarity(X[-1:], X[:-1]).ravel()
    top_idx = np.argsort(sims)[-8:][::-1]

    top_docs = [docs[i] for i in top_idx if sims[i] > 0.05]
    regions_mentioned = []
    issues = []
    for t, text in top_docs:
        if t in ("alert", "chi", "event"):
            # naive region extraction [region]
            if text.startswith("[") and "]" in text:
                regions_mentioned.append(text[1:text.index("]")])
        if t in ("alert", "event"):
            issues.append(text)

    # Craft a concise summary
    regions_uniq = sorted(set(regions_mentioned))
    summary = "Top regions: " + (", ".join(regions_uniq) if regions_uniq else "No hotspots.")
    drivers = {"evidence": [t + ": " + txt for t, txt in top_docs[:5]]}
    actions = [
        "Check tower health and restart impacted cells",
        "Notify customers in affected regions",
        "Open incident and assign on-call engineer",
    ]

    # If a Groq API is configured, call it to produce a concise answer + recommendations.
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")  # default to a fast model
    
    # Validate API key (check if it's a placeholder)
    if groq_key and (groq_key == "your-groq-api-key-here" or groq_key.strip() == ""):
        groq_key = None

    # Build evidence block for the prompt
    evidence_lines = [f"[{t}] {txt}" for t, txt in top_docs[:12]]
    system_prompt = (
        "You are an incident-assistant for T-Mobile's Customer Happiness Index (CHI) system. "
        "You help engineers understand customer sentiment, regional issues, and provide actionable recommendations. "
        "Always respond with a JSON object containing two keys: \"summary\" (a concise answer to the question) "
        "and \"recommendations\" (an array of 2-4 short, actionable recommendation strings). "
        "Only return valid JSON, no additional text."
    )
    user_prompt = (
        "Evidence from recent alerts, events, and CHI data:\n" + "\n".join(evidence_lines) + "\n\n"
        f"Question: {question}\n\n"
        "Provide your response as a JSON object with 'summary' and 'recommendations' keys."
    )

    if groq_key:
        print(f"[Groq API] API key found, attempting to use Groq AI (model: {groq_model})")
        try:
            # Use Groq's OpenAI-compatible API endpoint
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            
            body = {
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 512,
                "response_format": {"type": "json_object"}  # Request JSON response
            }

            resp = requests.post(groq_url, headers=headers, json=body, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            
            # Debug: Log successful API call
            print(f"[Groq API] Successfully called Groq API with model: {groq_model}")

            # Extract content from Groq's response format
            text_out = None
            if isinstance(data, dict) and "choices" in data:
                choices = data["choices"]
                if choices and isinstance(choices, list) and len(choices) > 0:
                    choice = choices[0]
                    if "message" in choice:
                        text_out = choice["message"].get("content")
                    elif "text" in choice:
                        text_out = choice.get("text")

            # Parse JSON from the model's response
            summary_text = None
            recommendations = []
            if text_out:
                try:
                    # Try to extract JSON from the response (might be wrapped in markdown code blocks)
                    text_clean = text_out.strip()
                    if "```json" in text_clean:
                        # Extract JSON from markdown code block
                        start = text_clean.find("```json") + 7
                        end = text_clean.find("```", start)
                        if end > start:
                            text_clean = text_clean[start:end].strip()
                    elif "```" in text_clean:
                        # Extract from generic code block
                        start = text_clean.find("```") + 3
                        end = text_clean.find("```", start)
                        if end > start:
                            text_clean = text_clean[start:end].strip()
                    
                    parsed = json.loads(text_clean)
                    if isinstance(parsed, dict):
                        summary_text = parsed.get("summary")
                        recommendations = parsed.get("recommendations", [])
                        if not isinstance(recommendations, list):
                            recommendations = []
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract summary from text
                    summary_text = text_out.strip()
                    # Try to find recommendations in the text
                    if "recommendations" in text_out.lower():
                        # Fallback: use the full text as summary
                        summary_text = text_out.strip()

            result = {
                "summary": summary_text or summary,
                "recommendations": recommendations if recommendations else actions,
                "drivers": drivers
            }
            return result
        except requests.exceptions.RequestException as e:
            # If the external call fails, fall back to retrieval-only response
            error_msg = f"Groq API error: {str(e)}"
            print(f"[Groq API ERROR] {error_msg}")
            print(f"[Groq API ERROR] Response status: {getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text[:200]
                    print(f"[Groq API ERROR] Response body: {error_detail}")
                except:
                    pass
            drivers["error"] = error_msg
            return {"summary": summary, "drivers": drivers, "actions": actions, "recommendations": actions}
        except Exception as e:
            # Catch any other errors
            error_msg = f"Groq call failed: {str(e)}"
            print(f"[Groq API ERROR] {error_msg}")
            import traceback
            print(f"[Groq API ERROR] Traceback: {traceback.format_exc()}")
            drivers["error"] = error_msg
            return {"summary": summary, "drivers": drivers, "actions": actions, "recommendations": actions}
    else:
        print("[Groq API] No valid API key found, using fallback mode")

    # No Groq configured — return the retrieval-only result
    return {"summary": summary, "drivers": drivers, "actions": actions, "recommendations": actions}


