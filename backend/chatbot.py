from __future__ import annotations
from datetime import datetime, timedelta
<<<<<<< HEAD
from typing import List, Tuple, Optional, Dict, Any
import os
import json

# Load environment variables early
try:
    from dotenv import load_dotenv
    import pathlib
    # Try loading from project root (one level up from backend/)
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    # Also try current directory
    load_dotenv(override=False)
except ImportError:
    pass  # dotenv not available, rely on system env vars
=======
from typing import List, Tuple
import os
import json
from pathlib import Path
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
<<<<<<< HEAD

from .models import Event, Alert, Runbook, CHI
try:
    from .vectorstore import query_text as pine_query
except Exception:  # pragma: no cover
    pine_query = None  # type: ignore
=======
import requests
from dotenv import load_dotenv

from .models import Event, Alert, Runbook, CHI

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95


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


<<<<<<< HEAD
def _get_state_from_region(region: str) -> str:
    """
    Extract state from region name if it's in format "City, ST" or "City, State".
    Returns state name or empty string.
    """
    # Common region formats: "Atlanta, GA", "Dallas, TX", "Chicago, IL"
    if ", " in region:
        state_abbr = region.split(", ")[-1].strip()
        # Map common abbreviations to full state names
        state_map = {
            "GA": "Georgia", "TX": "Texas", "IL": "Illinois", "PA": "Pennsylvania",
            "NY": "New York", "CA": "California", "FL": "Florida", "MA": "Massachusetts",
            "WA": "Washington", "AZ": "Arizona", "CO": "Colorado", "NC": "North Carolina"
        }
        return state_map.get(state_abbr.upper(), state_abbr)
    return ""


def _answer_chi_query(db: Session, question: str, query_type: str) -> dict:
    """
    Answer questions about highest/lowest CHI by querying the database.
    Returns actual city/region with CHI score.
    """
    from .models import CHI
    from sqlalchemy import select, desc
    
    # Get latest CHI for each region
    regions_data = []
    all_regions = db.scalars(select(CHI.region).distinct()).all()
    
    for region in all_regions:
        latest = db.scalars(
            select(CHI)
            .where(CHI.region == region)
            .order_by(desc(CHI.ts))
            .limit(1)
        ).first()
        if latest:
            regions_data.append({
                "region": region,
                "chi": latest.score,
                "ts": latest.ts
            })
    
    if not regions_data:
        return {
            "summary": "No CHI data available at this time. Please check back later.",
            "drivers": {"evidence": []},
            "actions": []
        }
    
    # Find highest or lowest
    if query_type == "highest":
        top_region = max(regions_data, key=lambda x: x["chi"])
        region_name = top_region["region"]
        chi_score = top_region["chi"]
        
        # Try to get state from region name (e.g., "Atlanta, GA" -> "Georgia")
        state = _get_state_from_region(region_name)
        location_str = f"{region_name}, {state}" if state else region_name
        
        summary = (
            f"The city with the highest CHI right now is **{location_str}** "
            f"with a CHI score of **{chi_score:.1f}**. "
            "This indicates stable network performance and strong customer sentiment in this region."
        )
    else:  # lowest
        low_region = min(regions_data, key=lambda x: x["chi"])
        region_name = low_region["region"]
        chi_score = low_region["chi"]
        
        state = _get_state_from_region(region_name)
        location_str = f"{region_name}, {state}" if state else region_name
        
        summary = (
            f"The lowest CHI is in **{location_str}** "
            f"with a CHI score of **{chi_score:.1f}**, indicating potential network issues "
            "or high customer dissatisfaction. Immediate investigation recommended."
        )
    
    return {
        "summary": summary,
        "drivers": {"evidence": []},
        "actions": [
            f"Review network performance metrics for {region_name}",
            "Check recent customer feedback and alerts",
            "Investigate any ongoing incidents or outages"
        ]
    }


def answer_question(db: Session, question: str) -> dict:
    """
    Simple chatbot: Query Pinecone for relevant data, then use GROQ to answer.
    Also handles direct CHI queries by querying the database.
    """
    question_lower = question.lower().strip()
    
    # Step 0: Handle direct CHI queries (highest/lowest CHI)
    if "highest chi" in question_lower or "top chi" in question_lower or "best chi" in question_lower:
        return _answer_chi_query(db, question, "highest")
    
    if "lowest chi" in question_lower or "worst chi" in question_lower or "bottom chi" in question_lower:
        return _answer_chi_query(db, question, "lowest")
    
    # Step 1: Query Pinecone for relevant customer reviews/data
    context_data = []
    if pine_query is not None:
        try:
            # Extract filters from question
            question_lower = question.lower()
            region_filter = None
            issue_type_filter = None
            
            # Simple region detection
            regions = ["atlanta", "chicago", "dallas", "houston", "philadelphia", "new york", 
                      "los angeles", "san antonio", "phoenix", "san diego", "miami", "boston"]
            for r in regions:
                if r in question_lower:
                    region_filter = r.capitalize()
                    break
            
            # Simple issue type detection
            if "roaming" in question_lower or "roam" in question_lower:
                issue_type_filter = "roaming"
            elif "billing" in question_lower or "bill" in question_lower or "charge" in question_lower:
                issue_type_filter = "billing"
            elif "coverage" in question_lower or "signal" in question_lower:
                issue_type_filter = "coverage"
            elif "slow" in question_lower or "speed" in question_lower:
                issue_type_filter = "slow_data"
            elif "support" in question_lower or "service" in question_lower:
                issue_type_filter = "customer_support"
            
            # Query Pinecone
            matches = pine_query(question, top_k=5, namespace="default", 
                               region_filter=region_filter, issue_type_filter=issue_type_filter)
            
            for m in matches:
                text = m.get("text", "").strip()
                metadata = m.get("metadata", {})
                if text:
                    context_data.append({
                        "text": text[:500],  # Limit length
                        "region": metadata.get("region", ""),
                        "rating": metadata.get("rating"),
                        "issue_type": metadata.get("issue_type", "")
                    })
        except Exception as e:
            print(f"[ERROR] Pinecone query failed: {e}")
    
    # Step 2: Use GROQ to generate answer from context
    return _simple_groq_answer(question, context_data)


def _simple_groq_answer(question: str, context_data: List[Dict[str, Any]]) -> dict:
    """
    Simple GROQ answer generator using context from Pinecone.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "summary": "GROQ API key not configured. Please set GROQ_API_KEY in your .env file.",
            "drivers": {"evidence": []},
            "actions": []
        }
    
    try:
        from .llm_client import get_groq_client
        client = get_groq_client()
    except ImportError:
        return {
            "summary": "GROQ library not installed. Run: pip install groq",
            "drivers": {"evidence": []},
            "actions": []
        }
    except RuntimeError as e:
        return {
            "summary": str(e),
            "drivers": {"evidence": []},
            "actions": []
        }
    except TypeError as te:
        # Catches the proxies kw error or any signature mismatch
        error_str = str(te).lower()
        if "proxies" in error_str or "unexpected keyword" in error_str:
            from .chatbot_fallback import best_match
            fallback_answer = best_match(question)
            return {
                "summary": fallback_answer,
                "drivers": {"evidence": []},
                "actions": []
            }
        raise te
    except Exception as e:
        # Network/key issues → graceful fallback
        from .chatbot_fallback import best_match
        fallback_answer = best_match(question)
        return {
            "summary": f"{fallback_answer} (Note: GROQ service temporarily unavailable: {str(e)})",
            "drivers": {"evidence": []},
            "actions": []
        }
    
    # Build context string from Pinecone data
    context_lines = []
    for item in context_data:
        text = item.get("text", "")
        region = item.get("region", "")
        rating = item.get("rating")
        issue = item.get("issue_type", "")
        
        line = text
        if region:
            line += f" [Region: {region}]"
        if rating is not None:
            line += f" [Rating: {rating}/5]"
        if issue:
            line += f" [Issue: {issue}]"
        context_lines.append(line)
    
    context = "\n".join(context_lines) if context_lines else "No specific context available."
    
    # Simple prompt
    system_msg = (
        "You are a helpful T-Mobile customer service assistant. "
        "Answer questions based on the provided customer review data. "
        "Return JSON with: summary (concise answer), drivers.evidence (list of relevant quotes), "
        "and actions (list of 3-5 recommendations)."
    )
    
    user_msg = f"Question: {question}\n\nCustomer Review Data:\n{context}\n\nProvide a helpful answer."
    
    try:
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content or ""
        parsed = _extract_json(content)
        
        if isinstance(parsed, dict):
            return {
                "summary": parsed.get("summary", "No summary available."),
                "drivers": {"evidence": parsed.get("drivers", {}).get("evidence", [])},
                "actions": parsed.get("actions", [])
            }
        else:
            # If JSON parsing fails, use raw content
            return {
                "summary": content[:500] if content else "No response generated.",
                "drivers": {"evidence": context_lines[:3]},
                "actions": []
            }
    except Exception as e:
        return {
            "summary": f"Error calling GROQ API: {str(e)}",
            "drivers": {"evidence": context_lines[:3] if context_lines else []},
            "actions": []
        }


def _try_answer_with_groq(question: str, top_docs: List[Tuple[str, str]], pine_metadata: Optional[List[Dict[str, Any]]] = None, db: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[DEBUG] GROQ_API_KEY not set, skipping GROQ")
        return None
    try:
        from .llm_client import get_groq_client
    except Exception as e:
        print(f"[DEBUG] Failed to import groq client: {e}")
        return None
    
    # Collect CHI data for general queries
    chi_data = ""
    if db is not None:
        try:
            from .models import CHI
            from sqlalchemy import select, desc
            chi_records = list(db.scalars(select(CHI).order_by(desc(CHI.ts)).limit(20)))
            if chi_records:
                chi_lines = []
                for chi in chi_records[:10]:
                    chi_lines.append(f"Region: {chi.region}, CHI: {chi.score:.1f}, Sentiment: {chi.sentiment:.2f}, KPI Health: {chi.kpi_health:.2f}")
                chi_data = "\n\nCurrent CHI (Customer Happiness Index) Data:\n" + "\n".join(chi_lines)
        except Exception:
            pass
    
    # Prepare context bullets with source attribution
    # PRIORITIZE Pinecone customer reviews over KPI/CHI data
    context_lines = []
    review_lines = []
    other_lines = []
    review_count = 0
    
    for doc_type, text in top_docs[:15]:  # Include more context
        if doc_type == "review":
            review_count += 1
            review_lines.append(f"- Customer Review #{review_count}: {text}")
        elif doc_type == "chi":
            other_lines.append(f"- CHI Data: {text}")
        else:
            other_lines.append(f"- {doc_type}: {text}")
    
    # Put reviews first, then other data
    context_lines = review_lines + other_lines
    # If no context, still let GROQ answer based on its knowledge
    context = "\n".join(context_lines) if context_lines else "No specific context available, but please answer based on your knowledge of T-Mobile operations."
    
    # Log context composition
    print(f"[DEBUG] Context: {len(review_lines)} reviews, {len(other_lines)} other docs")
    
    # Add metadata summary if available
    metadata_summary = ""
    if pine_metadata:
        regions = [m.get("region") for m in pine_metadata if m.get("region") and m.get("region") != "Unknown"]
        avg_rating = sum([m.get("rating", 0) for m in pine_metadata if m.get("rating")]) / max(1, len([m for m in pine_metadata if m.get("rating")]))
        if regions:
            metadata_summary = f"\n\nNote: Found {len(pine_metadata)} relevant customer reviews from regions: {', '.join(set(regions)[:5])}. Average rating: {avg_rating:.1f}/5."
    
    # Determine if this is a general query or review-focused query
    question_lower = question.lower()
    is_general_query = any(word in question_lower for word in ["which", "what", "highest", "lowest", "compare", "chi", "city", "region", "best", "worst", "how many"])
    has_reviews = len([d for d in top_docs if d[0] == "review"]) > 0
    
    # Always use GROQ to generate intelligent answers, even without specific context
    if is_general_query and not has_reviews:
        # General operational query
        system_msg = (
            "You are an AI assistant for T-Mobile customer operations. You analyze operational data "
            "including CHI (Customer Happiness Index) scores, alerts, and regional performance to answer questions. "
            "If specific data is provided, use it. If not, provide a helpful answer based on your knowledge. "
            "NEVER use predetermined or generic fallback messages. Always provide a real, intelligent answer. "
            "Respond in strict JSON with keys: "
            "summary (string - concise, accurate answer to the question, under 150 words. DO NOT say 'No customer reviews found' or 'Found operational data from X'. Provide an actual answer.), "
            "drivers (object with key 'evidence' -> list of strings with relevant data points or insights), "
            "and actions (list of 3-5 actionable recommendations based on the question). "
            "Be specific and cite actual numbers/regions from the data if provided, otherwise provide general guidance."
        )
        user_msg = (
            f"Question: {question}\n\n"
            f"Available Data:\n{context}{chi_data}\n\n"
            "Return only valid JSON. Provide an intelligent, helpful answer. Do not use generic fallback messages."
        )
    else:
        # Review-focused or mixed query
        # PRIORITIZE customer reviews in the prompt
        if review_lines:
            reviews_section = "\n\nCUSTOMER REVIEWS (PRIORITY - Use these first):\n" + "\n".join(review_lines)
            other_section = "\n\nAdditional Operational Data:\n" + "\n".join(other_lines) if other_lines else ""
        else:
            reviews_section = ""
            other_section = "\n\nOperational Data:\n" + context
        
    system_msg = (
            "You are an AI assistant for T-Mobile customer operations. You analyze customer feedback "
            "from reviews, support tickets, and operational data to provide insights. "
            "CRITICAL: When customer reviews are available, you MUST prioritize them and include the actual "
            "customer review text in the 'evidence' array. Quote the exact customer reviews verbatim. "
            "For negative reviews (rating < 3), generate specific recommendations to address the issues. "
            "If the user asks 'what do customers think', you MUST surface at least one customer review quote. "
            "NEVER use predetermined or generic fallback messages like 'No customer reviews found' or 'Found operational data from X'. "
            "Always provide a real, intelligent answer based on available data or your knowledge. "
            "Respond in strict JSON with keys: "
            "summary (string - concise answer under 150 words that references specific data/quotes. DO NOT say 'No customer reviews found'. Provide an actual answer.), "
            "drivers (object with key 'evidence' -> list of strings. Include customer review quotes with format: "
            "'Customer from [Region] (Rating: X/5): \"[exact review text]\"' when available), "
            "and actions (list of 3-5 SPECIFIC, ACTIONABLE recommendations. For negative reviews, focus on "
            "addressing the specific problems mentioned - e.g., roaming issues -> roaming partner actions, "
            "billing issues -> billing audit actions, coverage issues -> network engineering actions). "
            "Always prioritize actionable recommendations for problematic reviews."
    )
    user_msg = (
            f"Question: {question}\n"
            f"{reviews_section}"
            f"{other_section}"
            f"{chi_data}"
            f"{metadata_summary}\n\n"
            "Return only valid JSON. If customer reviews are available, include at least one review quote in evidence. "
            "For negative reviews, provide specific recommendations to address the issues."
    )
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    print(f"[DEBUG] Creating Groq client with API key (length: {len(api_key) if api_key else 0})")
    print(f"[DEBUG] Groq library version check...")
    try:
        import groq
        print(f"[DEBUG] groq version: {getattr(groq, '__version__', 'unknown')}")
    except:
        pass
    
    try:
        # Use the helper function that doesn't pass proxies
        print(f"[DEBUG] Creating Groq client using get_groq_client()")
        client = get_groq_client()
        print(f"[DEBUG] Groq client created successfully")
    except TypeError as te:
        # Catches the proxies kw error or any signature mismatch
        error_str = str(te).lower()
        if "proxies" in error_str or "unexpected keyword" in error_str:
            print(f"[DEBUG] Proxies error detected, using fallback")
            from .chatbot_fallback import best_match
            fallback_answer = best_match(question)
            return {
                "summary": fallback_answer,
                "drivers": {"evidence": []},
                "actions": []
            }
        raise te
    except Exception as e:
        print(f"[DEBUG] Error creating Groq client: {e}")
        from .chatbot_fallback import best_match
        fallback_answer = best_match(question)
        return {
            "summary": f"{fallback_answer} (Note: GROQ service temporarily unavailable)",
            "drivers": {"evidence": []},
            "actions": []
        }
    
    # Now make the API call (client is created at this point)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or ""
        print(f"[DEBUG] GROQ response received, length: {len(content)}")
        print(f"[DEBUG] GROQ full response: {content}")
        
        # Attempt to extract JSON
        parsed = _extract_json(content)
        if not isinstance(parsed, dict):
            print(f"[DEBUG] JSON parsing failed, using raw content as answer")
            print(f"[DEBUG] Content that failed to parse: {content[:500]}")
            # If JSON parsing fails, use the raw content as the answer
            # This ensures GROQ always provides an answer even if JSON parsing fails
            # Try to extract a reasonable summary from the content
            summary_text = content
            # Remove markdown code blocks if present
            if "```" in summary_text:
                parts = summary_text.split("```")
                summary_text = " ".join([p for p in parts if p.strip() and not p.strip().startswith("json")])
            
            return {
                "summary": summary_text[:1000] if summary_text else "No response generated.",
                "drivers": {"evidence": context_lines[:5] if context_lines else [f"GROQ response: {content[:200]}"]},
                "actions": []
            }
        summary = str(parsed.get("summary") or "").strip()
        evidence = parsed.get("drivers", {}).get("evidence") if isinstance(parsed.get("drivers"), dict) else None
        actions = parsed.get("actions")
        if not isinstance(evidence, list):
            evidence = context_lines[:5]
        if not isinstance(actions, list):
            actions = []
        return {"summary": summary or "No summary generated.", "drivers": {"evidence": evidence}, "actions": actions}
    except Exception as e:
        # Log error for debugging but don't crash
        import traceback
        print(f"[ERROR] GROQ error: {e}")
        print(f"[ERROR] GROQ error type: {type(e).__name__}")
        traceback.print_exc()
        # Instead of returning None, return a helpful error response
        # This ensures the user always gets an answer, even if GROQ fails
        error_msg = str(e)[:200] if str(e) else "Unknown error"
        return {
            "summary": f"I encountered an error while processing your question: '{question}'. The GROQ API call failed with error: {error_msg}. Please check the backend logs for more details.",
            "drivers": {"evidence": [f"Error: {type(e).__name__}: {error_msg}"]},
            "actions": ["Check backend logs for detailed error information", "Verify GROQ API key is valid and has sufficient credits", "Try rephrasing your question"]
        }


def _generate_dynamic_recommendations(question: str, issues: List[str], regions: List[str], avg_rating: Optional[float]) -> List[str]:
    """
    Generate dynamic recommendations based on the question, issues found, regions, and ratings.
    """
    question_lower = question.lower()
    recommendations = []
    
    # Normalize issue types (handle both "roaming" and "slow_data" formats)
    issues_normalized = [issue.lower().replace("_", " ") for issue in issues]
    all_issues_text = " ".join(issues_normalized) + " " + question_lower
    
    # Issue-specific recommendations (check both issue types and question)
    if "roaming" in all_issues_text:
        recommendations.extend([
            "Review roaming partner agreements and network handoff configurations",
            "Check for roaming coverage gaps in affected regions",
            "Investigate roaming data usage patterns and billing accuracy",
            "Update roaming partner profiles and verify APN settings"
        ])
    elif "billing" in all_issues_text or "charge" in all_issues_text:
        recommendations.extend([
            "Audit billing system for incorrect charges",
            "Review customer billing history for discrepancies",
            "Implement billing dispute resolution process"
        ])
    elif "coverage" in all_issues_text or "signal" in all_issues_text:
        recommendations.extend([
            "Deploy network engineers to assess signal strength in affected areas",
            "Check tower health and coverage maps for gaps",
            "Plan tower upgrades or new installations in coverage-deficient regions"
        ])
    elif "slow" in all_issues_text or "speed" in all_issues_text or "data speed" in all_issues_text or "throttl" in all_issues_text:
        recommendations.extend([
            "Analyze network congestion and capacity in affected regions",
            "Upgrade network infrastructure to support higher data speeds",
            "Optimize cell tower configurations for better performance",
            "Inspect congestion KPIs (PRB/throughput) and optimize QoS"
        ])
    elif "customer support" in all_issues_text or "customer service" in all_issues_text or "support" in all_issues_text:
        recommendations.extend([
            "Review customer service training and response times",
            "Implement customer feedback loop for service improvements",
            "Enhance support channel availability and quality",
            "Review ticket aging SLA and enable supervisor callback"
        ])
    
    # Rating-based recommendations
    if avg_rating is not None and avg_rating < 3.0:
        recommendations.append("Immediate escalation: Low customer satisfaction detected - prioritize issue resolution")
    
    # Region-specific recommendations
    if regions:
        recommendations.append(f"Focus investigation on regions: {', '.join(regions[:3])}")
    
    # Default recommendations if nothing specific found
    if not recommendations:
        recommendations = [
            "Analyze customer feedback patterns to identify root causes",
            "Engage with affected customers to gather more details",
            "Monitor metrics and implement targeted improvements"
        ]
    
    # Ensure we have 3-5 recommendations
    return recommendations[:5]


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    # Handle raw JSON or JSON fenced in code blocks
    if not text or not text.strip():
        return None
    candidate = text.strip()
    if "```" in candidate:
        # take content inside first code fence
        parts = candidate.split("```")
        if len(parts) >= 3:
            candidate = parts[1]
            # remove optional language tag on first line
            first_newline = candidate.find("\n")
            if first_newline != -1 and "{" not in candidate[:first_newline]:
                candidate = candidate[first_newline + 1 :]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Try to find JSON object if it's embedded in text
        start_idx = candidate.find('{')
        end_idx = candidate.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(candidate[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[DEBUG] _extract_json error: {e}")
        return None


def generate_alert_recommendations(
    db: Session,
    region: str,
    chi_before: Optional[float],
    chi_after: float,
    reason: str,
    top_k_docs: int = 5,
) -> Dict[str, Any]:
    """
    Use GROQ with Pinecone context (if available) plus latest CHI drivers to generate
    actionable recommendations for a single alert.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        analysis = f"CHI changed from {chi_before if chi_before is not None else '?'} to {chi_after:.1f} in {region}. Reason: {reason}."
        return {
            "analysis": analysis,
            "preview": "Investigate towers, validate KPIs, and communicate to customers.",
            "actions": [
                "Check tower health and KPIs in the affected region",
                "Notify customers via proactive message",
                "Escalate to NOC if impact sustains >30 minutes",
            ],
        }
    # Collect drivers for region
    drivers_lines: List[str] = []
    row = db.scalars(
        select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(1)
    ).first()
    if row and (row.drivers_json or {}):
        drv = row.drivers_json or {}
        top_kw = ", ".join((drv.get("top_keywords") or [])[:5])
        drivers_lines.append(f"drivers sentiment={drv.get('sentiment', 0):.2f} kpi={drv.get('kpi_health', 0):.2f} top={top_kw}")
    # Retrieve Pinecone docs
    pine_lines: List[str] = []
    if pine_query is not None:
        try:
            q = f"{region}: {reason}"
            matches = pine_query(q, top_k=top_k_docs, namespace="default")
            for m in matches:
                txt = (m.get("text") or "").strip()
                if txt:
                    pine_lines.append(txt[:300])
        except Exception:
            pass
    # Build prompt
    context_lines = [
        f"region: {region}",
        f"chi_before: {'' if chi_before is None else f'{chi_before:.1f}'}",
        f"chi_after: {chi_after:.1f}",
        f"reason: {reason}",
    ]
    context_lines += [f"chi_{line}" for line in drivers_lines]
    context_lines += [f"doc: {t}" for t in pine_lines]
    context = "\n".join(context_lines)
    system_msg = (
        "You are a telecom site reliability assistant. Based on the provided context, "
        "return strictly JSON with keys: "
        "'analysis' (2-5 sentences explaining likely cause/impact), "
        "'preview' (one concise sentence summary of next best step), "
        "and 'actions' (list of 3-6 short imperative recommendations). "
        "Be specific and avoid speculation."
    )
    user_msg = f"Context:\n{context}\n\nReturn only JSON with keys analysis, preview, actions."
    try:
        from .llm_client import get_groq_client
        # Use helper function that doesn't pass proxies
        client = get_groq_client()
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or ""
        parsed = _extract_json(content) or {}
        analysis = str(parsed.get("analysis") or "").strip()
        preview = str(parsed.get("preview") or "").strip()
        actions = parsed.get("actions")
        if isinstance(actions, list) and actions:
            return {
                "analysis": analysis or f"CHI changed from {chi_before if chi_before is not None else '?'} to {chi_after:.1f} in {region}. Reason: {reason}.",
                "preview": preview or "Validate KPIs and initiate mitigation steps.",
                "actions": [str(a) for a in actions][:6],
            }
    except Exception:
        pass
    # Fallback
    analysis = f"CHI changed from {chi_before if chi_before is not None else '?'} to {chi_after:.1f} in {region}. Reason: {reason}."
    return {
        "analysis": analysis,
        "preview": "Validate KPIs and initiate mitigation steps.",
        "actions": [
            "Validate recent KPI shifts (throughput/latency) at impacted sites",
            "Run congestion/runbook steps and re-route traffic where possible",
            "Notify customers in the region with ETA and mitigations",
            "Open incident and assign on-call engineer for triage",
        ],
    }
=======
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

>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95

