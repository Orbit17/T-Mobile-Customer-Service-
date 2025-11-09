from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .models import Event, Alert, Runbook, CHI


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
    return {"summary": summary, "drivers": drivers, "actions": actions}


