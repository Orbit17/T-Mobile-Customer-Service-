from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, desc, text
from sqlalchemy.orm import Session

from .database import init_db, get_db
from .models import Event, KPI, CHI, Alert
from .ingest import ensure_sources
from .chi import recompute_and_store_chi, compute_chi_for_region
from .alerts import generate_alerts_for_regions
from .simulator import simulate_outage
from .chatbot import answer_question
from .predict import forecast_chi
from .ingest import main as ingest_main
from .utils import clean_text, compute_sentiment, extract_keywords_texts, classify_topic_from_keywords
from .ingest import seed_events, seed_kpis, seed_runbook, ensure_sources


app = FastAPI(title="T-Mobile CHI MVP", version="0.1.0")


class IngestEvent(BaseModel):
    ts: Optional[str] = None
    region: str
    source: Optional[str] = None
    text: str
    rating: Optional[float] = None


class SimulateRequest(BaseModel):
    region: str
    impact_percent: int = 50
    duration_minutes: int = 30
    event_rate_per_minute: int = 3


class QARequest(BaseModel):
    question: str


@app.on_event("startup")
def startup() -> None:
    init_db()
    # ensure default sources exist
    with next(get_db()) as db:
        ensure_sources(db)


@app.post("/ingest")
def ingest_event(payload: IngestEvent, db: Session = Depends(get_db)) -> dict:
    ts = datetime.fromisoformat(payload.ts) if payload.ts else datetime.utcnow()
    text_clean = clean_text(payload.text or "")
    sentiment = compute_sentiment(text_clean)
    keywords_list = extract_keywords_texts([text_clean], top_k=5)
    keywords = keywords_list[0] if keywords_list else []
    topic = classify_topic_from_keywords(keywords)
    e = Event(
        ts=ts,
        region=payload.region,
        source_id=None,
        text=text_clean,
        rating=payload.rating,
        keywords=keywords,
        sentiment=sentiment,
        topic=topic,
    )
    db.add(e)
    db.commit()
    return {"status": "ok", "id": e.id}


@app.get("/chi")
def get_chi(region: str = Query(...), db: Session = Depends(get_db)) -> dict:
    # If we have a recent CHI (<=5 minutes), return it; otherwise recompute
    row = db.scalars(
        select(CHI)
        .where(CHI.region == region)
        .order_by(desc(CHI.ts))
        .limit(1)
    ).first()
    if row and (datetime.utcnow() - row.ts) <= timedelta(minutes=5):
        drivers = row.drivers_json or {}
        forecast = forecast_chi(db, region)
        return {"region": region, "score": row.score, "drivers": drivers, "forecast": [(t.isoformat(), s) for t, s in forecast]}
    # recompute on demand
    score, drivers = compute_chi_for_region(db, region)
    new_row = CHI(ts=datetime.utcnow(), region=region, score=score, drivers_json=drivers)
    db.add(new_row)
    db.commit()
    forecast = forecast_chi(db, region)
    return {"region": region, "score": score, "drivers": drivers, "forecast": [(t.isoformat(), s) for t, s in forecast]}


@app.get("/regions")
def get_regions_summary(db: Session = Depends(get_db)) -> dict:
    # Return latest CHI per region
    rows = db.execute(
        text(
            """
        SELECT c1.region, c1.score, c1.ts
        FROM chi c1
        JOIN (
            SELECT region, MAX(ts) as max_ts
            FROM chi
            GROUP BY region
        ) c2 ON c1.region = c2.region AND c1.ts = c2.max_ts
        """
        )
    ).fetchall()
    regions = [{"region": r[0], "score": float(r[1]), "ts": str(r[2])} for r in rows]
    return {"regions": regions}


@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db)) -> dict:
    rows = list(
        db.scalars(select(Alert).order_by(desc(Alert.ts)).limit(50))
    )
    return {
        "alerts": [
            {
                "id": a.id,
                "ts": a.ts.isoformat(),
                "region": a.region,
                "chi_before": a.chi_before,
                "chi_after": a.chi_after,
                "reason": a.reason,
                "recommendation": a.recommendation,
            }
            for a in rows
        ]
    }


@app.post("/simulate")
def post_simulate(payload: SimulateRequest, db: Session = Depends(get_db)) -> dict:
    simulate_outage(
        db,
        region=payload.region,
        impact_percent=payload.impact_percent,
        duration_minutes=payload.duration_minutes,
        event_rate_per_minute=payload.event_rate_per_minute,
    )
    # recompute CHI and generate alerts
    recompute_and_store_chi(db, [payload.region])
    alerts = generate_alerts_for_regions(db, [payload.region])
    return {"status": "ok", "alerts_created": len(alerts)}


@app.post("/qa")
def post_qa(payload: QARequest, db: Session = Depends(get_db)) -> dict:
    result = answer_question(db, payload.question)
    return result


@app.post("/seed")
def post_seed(db: Session = Depends(get_db)) -> dict:
    """
    Load seed CSV data server-side.
    """
    try:
        # Use current session to avoid re-init issues and surface precise errors
        ensure_sources(db)
        events_created = seed_events(db)
        kpis_created = seed_kpis(db)
        runbooks_created = seed_runbook(db)
        return {
            "status": "ok",
            "seeded": True,
            "counts": {"events": events_created, "kpis": kpis_created, "runbook": runbooks_created},
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/kudos")
def get_kudos(db: Session = Depends(get_db)) -> dict:
    """
    Return recent positive events (kudos).
    """
    rows = list(
        db.scalars(
            select(Event)
            .where(Event.sentiment != None)  # noqa: E711
            .order_by(desc(Event.ts))
            .limit(200)
        )
    )
    kudos = [e for e in rows if (e.sentiment or 0) > 0.6]
    return {
        "kudos": [
            {"ts": e.ts.isoformat(), "region": e.region, "text": e.text, "sentiment": e.sentiment}
            for e in kudos[:50]
        ]
    }


class RecomputeRequest(BaseModel):
    regions: List[str]


@app.post("/recompute")
def post_recompute(payload: RecomputeRequest, db: Session = Depends(get_db)) -> dict:
    """
    Recompute CHI for provided regions and generate alerts.
    """
    if not payload.regions:
        return {"status": "error", "message": "regions list required"}
    recompute_and_store_chi(db, payload.regions)
    alerts = generate_alerts_for_regions(db, payload.regions)
    return {"status": "ok", "alerts_created": len(alerts)}


