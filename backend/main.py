from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
<<<<<<< HEAD

from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
=======
from pathlib import Path

from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
from pydantic import BaseModel
from sqlalchemy import select, desc, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import init_db, get_db
<<<<<<< HEAD
=======

# Load environment variables from .env file at startup
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
from .models import Event, KPI, CHI, Alert
from .ingest import ensure_sources
from .chi import recompute_and_store_chi, compute_chi_for_region
from .alerts import generate_alerts_for_regions
from .simulator import simulate_outage
<<<<<<< HEAD
from .chatbot import answer_question, generate_alert_recommendations
from .predict import forecast_chi
from .api_chat import router as chat_router
from .ingest import main as ingest_main
from .utils import clean_text, compute_sentiment, extract_keywords_texts, classify_topic_from_keywords
from .ingest import seed_events, seed_kpis, seed_runbook, ensure_sources
import json
from pathlib import Path
import os
from datetime import timedelta as _timedelta


app = FastAPI(title="T-Mobile CHI", version="0.1.0")

# Add CORS middleware to allow React app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
=======
from .chatbot import answer_question
from .predict import forecast_chi
from .alert_recommendations import generate_ai_recommendations_for_alert, generate_detailed_analysis_for_alert
from .ingest import main as ingest_main
from .utils import clean_text, compute_sentiment, extract_keywords_texts, classify_topic_from_keywords
from .ingest import seed_events, seed_kpis, seed_runbook, ensure_sources


app = FastAPI(title="T-Mobile CHI MVP", version="0.1.0")
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95


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


<<<<<<< HEAD
class IngestDocsRequest(BaseModel):
    documents: List[str]
    namespace: Optional[str] = "default"

class IngestReviewsRequest(BaseModel):
    path: Optional[str] = None
    to_pinecone: bool = True
    to_db: bool = True
    namespace: Optional[str] = "default"

@app.on_event("startup")
def startup() -> None:
    # Load .env from project root (one level up from backend/)
    import pathlib
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    # Also try loading from current directory
    load_dotenv(override=False)
=======
@app.on_event("startup")
def startup() -> None:
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
    init_db()
    # ensure default sources exist
    with next(get_db()) as db:
        ensure_sources(db)

<<<<<<< HEAD
try:
    from .vectorstore import upsert_texts, upsert_items, chunk_text, query_text
except Exception:
    upsert_texts = None  # type: ignore
    upsert_items = None  # type: ignore
    chunk_text = None  # type: ignore
    query_text = None  # type: ignore

=======
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95

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


<<<<<<< HEAD
@app.post("/ingest_docs")
def ingest_docs(payload: IngestDocsRequest) -> dict:
    if upsert_texts is None:
        return {"status": "error", "message": "Vector store not available"}
    docs = [d for d in (payload.documents or []) if (d or "").strip()]
    if not docs:
        return {"status": "error", "message": "No documents provided"}
    try:
        count = upsert_texts(docs, namespace=payload.namespace or "default")
        return {"status": "ok", "upserted": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/ingest_reviews")
def ingest_reviews(payload: IngestReviewsRequest, db: Session = Depends(get_db)) -> dict:
    """
    Ingest JSONL reviews into the SQL DB (to recompute CHI) and Pinecone vector index for RAG.
    JSONL lines must contain at least: {"text": "...", "metadata": {...}}.
    """
    reviews_path = payload.path or str(Path(os.getenv("REVIEWS_JSONL_PATH", "")).expanduser())
    if not reviews_path:
        return {"status": "error", "message": "Provide 'path' or set REVIEWS_JSONL_PATH"}
    p = Path(reviews_path).expanduser()
    if not p.exists():
        return {"status": "error", "message": f"File not found: {p}"}
    # Load lines
    lines = p.read_text(encoding="utf-8").splitlines()
    records: List[Dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict) and ("text" in rec):
                records.append(rec)
        except Exception:
            continue
    if not records:
        return {"status": "error", "message": "No valid records found in file"}
    upserted_vectors = 0
    regions_changed: List[str] = []
    # Upsert to Pinecone
    if payload.to_pinecone:
        if upsert_items is None or chunk_text is None:
            return {"status": "error", "message": "Vector store not available"}
        items = []
        for rec in records:
            text = (rec.get("text") or "").strip()
            metadata = rec.get("metadata") or {}
            for chunk in chunk_text(text, chunk_size=800, overlap=120):
                items.append({"text": chunk, "metadata": metadata})
        if items:
            upserted_vectors = upsert_items(items, namespace=payload.namespace or "default")
    # Insert into DB as Events and recompute CHI
    if payload.to_db:
        for rec in records:
            meta = rec.get("metadata") or {}
            region = meta.get("region") or "Unknown"
            text_clean = clean_text(rec.get("text") or "")
            sentiment = compute_sentiment(text_clean)
            keywords_list = extract_keywords_texts([text_clean], top_k=5)
            keywords = keywords_list[0] if keywords_list else []
            topic = classify_topic_from_keywords(keywords)
            e = Event(
                ts=datetime.utcnow(),
                region=region,
                source_id=None,
                text=text_clean,
                rating=float(meta.get("rating")) if meta.get("rating") is not None else None,
                keywords=keywords,
                sentiment=sentiment,
                topic=topic,
            )
            db.add(e)
            if region not in regions_changed:
                regions_changed.append(region)
        db.commit()
        if regions_changed:
            recompute_and_store_chi(db, regions_changed)
            generate_alerts_for_regions(db, regions_changed)
    return {
        "status": "ok",
        "vectors_upserted": upserted_vectors,
        "regions_updated": regions_changed,
        "count_records": len(records),
    }


@app.get("/sentiment_overall")
def get_sentiment_overall(hours: int = Query(24), db: Session = Depends(get_db)) -> dict:
    """
    Average sentiment across events for the last `hours`.
    Sentiment values are in [-1, 1]. We map to [0, 100] for display.
    """
    now = datetime.utcnow()
    start = now - _timedelta(hours=max(1, min(hours, 168)))
    rows = list(
        db.scalars(
            select(Event.sentiment)
            .where(Event.ts >= start)
            .where(Event.sentiment != None)  # noqa: E711
            .order_by(desc(Event.ts))
        )
    )
    if not rows:
        return {"score": 50.0, "samples": 0, "window_hours": hours}
    vals = [float(s) for s in rows if s is not None]
    avg = sum(vals) / max(1, len(vals))
    score = (avg + 1.0) * 50.0  # map [-1,1] -> [0,100]
    return {"score": round(score, 1), "samples": len(vals), "window_hours": hours}

=======
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
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
<<<<<<< HEAD
def get_alerts(
    region: Optional[str] = Query(None),
    start: Optional[str] = Query(None, description="ISO datetime, e.g. 2025-11-09T00:00:00"),
    end: Optional[str] = Query(None, description="ISO datetime"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Return recent alerts. Optional filters:
    - region: filter by region name
    - start, end: ISO datetimes to bound by ts
    """
    conditions = []
    if region:
        conditions.append(Alert.region == region)
    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            conditions.append(Alert.ts >= start_dt)
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            conditions.append(Alert.ts <= end_dt)
        except Exception:
            pass
    query = select(Alert)
    if conditions:
        query = query.where(*conditions)
    query = query.order_by(desc(Alert.ts)).limit(200)
    rows = list(db.scalars(query))
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
=======
def get_alerts(db: Session = Depends(get_db), include_ai_recommendations: bool = Query(False)) -> dict:
    rows = list(
        db.scalars(select(Alert).order_by(desc(Alert.ts)).limit(50))
    )
    alerts_list = []
    for a in rows:
        alert_dict = {
            "id": a.id,
            "ts": a.ts.isoformat(),
            "region": a.region,
            "chi_before": a.chi_before,
            "chi_after": a.chi_after,
            "reason": a.reason,
            "recommendation": a.recommendation,
        }
        
        # Generate AI recommendations if requested
        if include_ai_recommendations:
            ai_recommendations = generate_ai_recommendations_for_alert(db, a)
            alert_dict["ai_recommendations"] = ai_recommendations
        
        alerts_list.append(alert_dict)
    
    return {"alerts": alerts_list}


@app.get("/alerts/{alert_id}/analysis")
def get_alert_analysis(alert_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Get detailed AI analysis for a specific alert.
    """
    alert = db.scalars(select(Alert).where(Alert.id == alert_id)).first()
    if not alert:
        return JSONResponse(status_code=404, content={"error": "Alert not found"})
    
    analysis = generate_detailed_analysis_for_alert(db, alert)
    return {
        "alert_id": alert_id,
        "region": alert.region,
        "ts": alert.ts.isoformat(),
        "chi_before": alert.chi_before,
        "chi_after": alert.chi_after,
        "reason": alert.reason,
        **analysis
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
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
<<<<<<< HEAD
    """Chat endpoint for AI assistant."""
=======
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
    result = answer_question(db, payload.question)
    return result


<<<<<<< HEAD
@app.get("/predict")
def get_predict(region: str = Query(...), db: Session = Depends(get_db)) -> dict:
    """
    Predictive analytics endpoint.
    Returns predicted CHI for next hour with confidence interval.
    """
    from .predict import forecast_chi
    
    # Get current CHI
    current_chi = db.scalars(
        select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(1)
    ).first()
    
    if not current_chi:
        return {
            "region": region,
            "current_chi": None,
            "predicted_chi": None,
            "confidence_interval": None,
            "trend": "unknown"
        }
    
    # Get forecast (next hour = 60 minutes)
    forecast = forecast_chi(db, region, horizon_minutes=60, step_minutes=15)
    
    if not forecast:
        return {
            "region": region,
            "current_chi": current_chi.score,
            "predicted_chi": current_chi.score,
            "confidence_interval": [current_chi.score - 5, current_chi.score + 5],
            "trend": "stable"
        }
    
    # Next hour prediction (last forecast point)
    predicted_chi = forecast[-1][1]
    current_score = current_chi.score
    
    # Calculate confidence interval (simplified - would use actual model uncertainty)
    std_dev = abs(predicted_chi - current_score) * 0.3  # 30% of change as uncertainty
    confidence_interval = [
        max(0, predicted_chi - std_dev),
        min(100, predicted_chi + std_dev)
    ]
    
    # Determine trend
    if predicted_chi > current_score + 2:
        trend = "improving"
    elif predicted_chi < current_score - 2:
        trend = "declining"
    else:
        trend = "stable"
    
    # Early warning if predicted CHI < 50
    early_warning = predicted_chi < 50
    
    return {
        "region": region,
        "current_chi": current_score,
        "predicted_chi": round(predicted_chi, 1),
        "confidence_interval": [round(ci, 1) for ci in confidence_interval],
        "trend": trend,
        "early_warning": early_warning,
        "forecast_points": [(t.isoformat(), round(s, 1)) for t, s in forecast]
    }


@app.get("/pinecone_status")
def get_pinecone_status() -> dict:
    """Check Pinecone connection and index status."""
    try:
        # Check if Pinecone SDK is available
        try:
            from pinecone import Pinecone
        except ImportError:
            return {
                "status": "error",
                "message": "Pinecone SDK not installed. Run: pip install pinecone",
                "api_key_set": bool(os.getenv("PINECONE_API_KEY"))
            }
        
        # Check if vectorstore module can be imported
        try:
            from .vectorstore import _get_index, _get_pinecone, _dim
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to import vectorstore module: {str(e)}. This may be due to missing dependencies. Try: pip install sentence-transformers huggingface-hub",
                "api_key_set": bool(os.getenv("PINECONE_API_KEY"))
            }
        
        # Try to get Pinecone client
        try:
            pc = _get_pinecone()
            index = _get_index()
            index_name = os.getenv("PINECONE_INDEX", "t-mobile")
            namespace = os.getenv("PINECONE_NAMESPACE", "default")
            
            # Try a simple query to verify connection
            try:
                from .vectorstore import query_text
                test_query = query_text("test", top_k=1, namespace=namespace) if query_text else []
            except Exception:
                test_query = []
            
            return {
                "status": "connected",
                "index": index_name,
                "namespace": namespace,
                "dimension": _dim if _dim else 1024,
                "metric": "cosine",
                "test_query_success": len(test_query) >= 0,
                "api_key_set": bool(os.getenv("PINECONE_API_KEY"))
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Pinecone connection error: {str(e)}",
                "api_key_set": bool(os.getenv("PINECONE_API_KEY"))
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "api_key_set": bool(os.getenv("PINECONE_API_KEY"))
        }


=======
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
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


<<<<<<< HEAD
# Include chat router for recommendations endpoint
app.include_router(chat_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

=======
>>>>>>> 50e2313a86442d215d6cdf6c59817b6a38090a95
