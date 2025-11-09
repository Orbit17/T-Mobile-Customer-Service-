from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .models import Alert, CHI, Event, KPI
from sqlalchemy import select, desc

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def generate_ai_recommendations_for_alert(db: Session, alert: Alert) -> List[str]:
    """
    Generate AI-powered recommendations for a specific alert using Groq API.
    Analyzes the alert context, recent events, CHI data, and KPIs to provide
    data-driven recommendations.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    # Validate API key
    if not groq_key or groq_key == "your-groq-api-key-here" or groq_key.strip() == "":
        return []  # Return empty if no API key
    
    # Collect context for the alert
    context_parts = []
    
    # Alert details
    context_parts.append(f"Alert Region: {alert.region}")
    context_parts.append(f"CHI dropped from {alert.chi_before:.1f} to {alert.chi_after:.1f}")
    context_parts.append(f"Reason: {alert.reason}")
    
    # Get recent CHI data for the region
    latest_chi = db.scalars(
        select(CHI).where(CHI.region == alert.region).order_by(desc(CHI.ts)).limit(1)
    ).first()
    
    if latest_chi and latest_chi.drivers_json:
        drivers = latest_chi.drivers_json
        context_parts.append(f"Sentiment: {drivers.get('sentiment', 0):.2f}")
        context_parts.append(f"Volume Z-score: {drivers.get('volume_z', 0):.2f}")
        if drivers.get('top_keywords'):
            context_parts.append(f"Top keywords: {', '.join(drivers.get('top_keywords', [])[:5])}")
    
    # Get recent events for the region (last 2 hours)
    recent_events = list(
        db.scalars(
            select(Event)
            .where(Event.region == alert.region)
            .where(Event.ts >= alert.ts - timedelta(hours=2))
            .order_by(desc(Event.ts))
            .limit(20)
        )
    )
    
    if recent_events:
        negative_events = [e for e in recent_events if (e.sentiment or 0) < -0.2]
        if negative_events:
            context_parts.append(f"Recent negative events: {len(negative_events)}")
            sample_texts = [e.text[:100] for e in negative_events[:3]]
            context_parts.append(f"Sample issues: {', '.join(sample_texts)}")
    
    # Get recent KPI data
    recent_kpis = list(
        db.scalars(
            select(KPI)
            .where(KPI.region == alert.region)
            .order_by(desc(KPI.ts))
            .limit(2)
        )
    )
    
    if len(recent_kpis) >= 2:
        latest_kpi, prev_kpi = recent_kpis[0], recent_kpis[1]
        if prev_kpi.download_mbps > 0:
            download_change = ((latest_kpi.download_mbps - prev_kpi.download_mbps) / prev_kpi.download_mbps) * 100
            context_parts.append(f"Download speed change: {download_change:.1f}%")
        if prev_kpi.latency_ms > 0:
            latency_change = ((latest_kpi.latency_ms - prev_kpi.latency_ms) / prev_kpi.latency_ms) * 100
            context_parts.append(f"Latency change: {latency_change:.1f}%")
    
    # Build the prompt
    context_text = "\n".join(context_parts)
    
    system_prompt = (
        "You are a network operations expert for T-Mobile. Analyze alert data and provide "
        "3-5 specific, actionable recommendations. Focus on data-driven insights and prioritize "
        "actions that will have the most impact. Return only a JSON object with a 'recommendations' "
        "array containing short recommendation strings (each 1-2 sentences)."
    )
    
    user_prompt = (
        f"Alert Context:\n{context_text}\n\n"
        f"Based on this alert data, provide specific recommendations to address the issue. "
        f"Consider the CHI drop, sentiment trends, recent events, and KPI changes. "
        f"Provide actionable steps that operations teams can take immediately."
    )
    
    try:
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
            "temperature": 0.3,
            "max_tokens": 400,
            "response_format": {"type": "json_object"}
        }
        
        resp = requests.post(groq_url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract content from Groq's response
        text_out = None
        if isinstance(data, dict) and "choices" in data:
            choices = data["choices"]
            if choices and isinstance(choices, list) and len(choices) > 0:
                choice = choices[0]
                if "message" in choice:
                    text_out = choice["message"].get("content")
        
        # Parse JSON from the model's response
        if text_out:
            try:
                # Try to extract JSON from markdown code blocks if present
                text_clean = text_out.strip()
                if "```json" in text_clean:
                    start = text_clean.find("```json") + 7
                    end = text_clean.find("```", start)
                    if end > start:
                        text_clean = text_clean[start:end].strip()
                elif "```" in text_clean:
                    start = text_clean.find("```") + 3
                    end = text_clean.find("```", start)
                    if end > start:
                        text_clean = text_clean[start:end].strip()
                
                parsed = json.loads(text_clean)
                if isinstance(parsed, dict):
                    recommendations = parsed.get("recommendations", [])
                    if isinstance(recommendations, list):
                        return recommendations
            except json.JSONDecodeError:
                pass
        
        return []
    except Exception as e:
        print(f"[Alert AI] Error generating recommendations: {str(e)}")
        return []


def generate_detailed_analysis_for_alert(db: Session, alert: Alert) -> dict:
    """
    Generate a comprehensive AI-powered analysis and tailored recommendations for a specific alert.
    Returns a detailed analysis including root cause analysis, impact assessment, and action plan.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    # Validate API key
    if not groq_key or groq_key == "your-groq-api-key-here" or groq_key.strip() == "":
        return {
            "analysis": "AI analysis unavailable. Please configure GROQ_API_KEY.",
            "recommendations": [],
            "root_causes": [],
            "impact_assessment": ""
        }
    
    # Collect comprehensive context for the alert
    context_parts = []
    
    # Alert details
    chi_drop = (alert.chi_before - alert.chi_after) if alert.chi_before else 0
    context_parts.append(f"=== ALERT DETAILS ===")
    context_parts.append(f"Region: {alert.region}")
    context_parts.append(f"Timestamp: {alert.ts.isoformat()}")
    context_parts.append(f"CHI dropped from {alert.chi_before:.1f} to {alert.chi_after:.1f} (drop of {chi_drop:.1f} points)")
    context_parts.append(f"Alert Reason: {alert.reason}")
    
    # Get recent CHI data for the region
    latest_chi = db.scalars(
        select(CHI).where(CHI.region == alert.region).order_by(desc(CHI.ts)).limit(1)
    ).first()
    
    if latest_chi and latest_chi.drivers_json:
        drivers = latest_chi.drivers_json
        context_parts.append(f"\n=== CHI DRIVERS ===")
        context_parts.append(f"Current Sentiment: {drivers.get('sentiment', 0):.2f} (range: -1 to 1)")
        context_parts.append(f"Volume Z-score: {drivers.get('volume_z', 0):.2f} (indicates volume spike if >2)")
        context_parts.append(f"KPI Health: {drivers.get('kpi_health', 0):.2f}")
        if drivers.get('top_keywords'):
            context_parts.append(f"Top Keywords: {', '.join(drivers.get('top_keywords', [])[:10])}")
    
    # Get CHI history (last 5 data points)
    chi_history = list(
        db.scalars(
            select(CHI)
            .where(CHI.region == alert.region)
            .order_by(desc(CHI.ts))
            .limit(5)
        )
    )
    if chi_history:
        context_parts.append(f"\n=== CHI TREND ===")
        for i, chi in enumerate(chi_history[:5]):
            context_parts.append(f"  {chi.ts.strftime('%Y-%m-%d %H:%M')}: {chi.score:.1f}")
    
    # Get recent events for the region (last 4 hours)
    recent_events = list(
        db.scalars(
            select(Event)
            .where(Event.region == alert.region)
            .where(Event.ts >= alert.ts - timedelta(hours=4))
            .order_by(desc(Event.ts))
            .limit(50)
        )
    )
    
    if recent_events:
        context_parts.append(f"\n=== RECENT EVENTS ({len(recent_events)} total) ===")
        negative_events = [e for e in recent_events if (e.sentiment or 0) < -0.2]
        positive_events = [e for e in recent_events if (e.sentiment or 0) > 0.2]
        neutral_events = [e for e in recent_events if -0.2 <= (e.sentiment or 0) <= 0.2]
        
        context_parts.append(f"Negative sentiment events: {len(negative_events)}")
        context_parts.append(f"Positive sentiment events: {len(positive_events)}")
        context_parts.append(f"Neutral events: {len(neutral_events)}")
        
        if negative_events:
            context_parts.append(f"\nSample negative events:")
            for e in negative_events[:5]:
                context_parts.append(f"  [{e.ts.strftime('%H:%M')}] Sentiment: {e.sentiment:.2f}, Topic: {e.topic or 'N/A'}")
                context_parts.append(f"    Text: {e.text[:150]}")
    
    # Get KPI history
    recent_kpis = list(
        db.scalars(
            select(KPI)
            .where(KPI.region == alert.region)
            .order_by(desc(KPI.ts))
            .limit(5)
        )
    )
    
    if len(recent_kpis) >= 2:
        context_parts.append(f"\n=== KPI METRICS ===")
        latest_kpi, prev_kpi = recent_kpis[0], recent_kpis[1]
        
        if prev_kpi.download_mbps > 0:
            download_change = ((latest_kpi.download_mbps - prev_kpi.download_mbps) / prev_kpi.download_mbps) * 100
            context_parts.append(f"Download Speed: {prev_kpi.download_mbps:.1f} → {latest_kpi.download_mbps:.1f} Mbps ({download_change:+.1f}%)")
        
        if prev_kpi.latency_ms > 0:
            latency_change = ((latest_kpi.latency_ms - prev_kpi.latency_ms) / prev_kpi.latency_ms) * 100
            context_parts.append(f"Latency: {prev_kpi.latency_ms:.1f} → {latest_kpi.latency_ms:.1f} ms ({latency_change:+.1f}%)")
    
    # Build the comprehensive prompt
    context_text = "\n".join(context_parts)
    
    system_prompt = (
        "You are a senior network operations analyst for T-Mobile. Analyze alert data comprehensively "
        "and provide a detailed technical analysis. Return a JSON object with these keys:\n"
        "- 'analysis': A detailed 3-4 paragraph analysis explaining what happened, why it happened, "
        "  and the significance of the issue\n"
        "- 'root_causes': An array of 2-4 likely root causes based on the data\n"
        "- 'impact_assessment': A brief assessment of customer impact and business impact\n"
        "- 'recommendations': An array of 5-7 specific, prioritized, actionable recommendations "
        "  with clear steps for the operations team\n"
        "Be specific, data-driven, and technical. Focus on actionable insights."
    )
    
    user_prompt = (
        f"Comprehensive Alert Data:\n{context_text}\n\n"
        f"Provide a detailed analysis of this alert. Include:\n"
        f"1. What happened (summary of the issue)\n"
        f"2. Why it likely happened (root cause analysis based on the data patterns)\n"
        f"3. Impact assessment (how this affects customers and operations)\n"
        f"4. Detailed, prioritized recommendations with specific action steps\n\n"
        f"Base your analysis on the actual data provided. Be specific about metrics, trends, and patterns."
    )
    
    try:
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
            "temperature": 0.3,
            "max_tokens": 1200,
            "response_format": {"type": "json_object"}
        }
        
        resp = requests.post(groq_url, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract content from Groq's response
        text_out = None
        if isinstance(data, dict) and "choices" in data:
            choices = data["choices"]
            if choices and isinstance(choices, list) and len(choices) > 0:
                choice = choices[0]
                if "message" in choice:
                    text_out = choice["message"].get("content")
        
        # Parse JSON from the model's response
        if text_out:
            try:
                # Try to extract JSON from markdown code blocks if present
                text_clean = text_out.strip()
                if "```json" in text_clean:
                    start = text_clean.find("```json") + 7
                    end = text_clean.find("```", start)
                    if end > start:
                        text_clean = text_clean[start:end].strip()
                elif "```" in text_clean:
                    start = text_clean.find("```") + 3
                    end = text_clean.find("```", start)
                    if end > start:
                        text_clean = text_clean[start:end].strip()
                
                parsed = json.loads(text_clean)
                if isinstance(parsed, dict):
                    return {
                        "analysis": parsed.get("analysis", "Analysis unavailable."),
                        "root_causes": parsed.get("root_causes", []),
                        "impact_assessment": parsed.get("impact_assessment", ""),
                        "recommendations": parsed.get("recommendations", [])
                    }
            except json.JSONDecodeError as e:
                print(f"[Alert AI] JSON decode error: {str(e)}")
        
        return {
            "analysis": "Failed to parse AI response.",
            "recommendations": [],
            "root_causes": [],
            "impact_assessment": ""
        }
    except Exception as e:
        print(f"[Alert AI] Error generating detailed analysis: {str(e)}")
        return {
            "analysis": f"Error generating analysis: {str(e)}",
            "recommendations": [],
            "root_causes": [],
            "impact_assessment": ""
        }

