from __future__ import annotations
from datetime import datetime, timedelta
from typing import List
import random

from sqlalchemy.orm import Session

from .models import Event, KPI
from .utils import clean_text, compute_sentiment


NEGATIVE_TEMPLATES = [
    "Massive outage in {region}! No service!",
    "Network down in {region}, can't make calls.",
    "Data is super slow in {region}, unusable.",
    "High latency and dropped calls in {region}.",
    "Terrible speeds in {region} after update.",
    "Anyone else having issues in {region}?",
]


def simulate_outage(
    db: Session,
    region: str,
    impact_percent: int = 50,
    duration_minutes: int = 30,
    event_rate_per_minute: int = 3,
) -> List[Event]:
    """
    Inject synthetic negative events and degrade KPIs. impact_percent reduces download and increases latency.
    """
    now = datetime.utcnow()
    created: List[Event] = []
    for i in range(duration_minutes):
        ts = now + timedelta(minutes=i)
        for _ in range(event_rate_per_minute):
            txt = random.choice(NEGATIVE_TEMPLATES).format(region=region)
            txt = clean_text(txt)
            sent = min(-0.5, compute_sentiment(txt) - 0.3)
            e = Event(
                ts=ts,
                region=region,
                source_id=None,
                text=txt,
                rating=None,
                keywords=["outage", "down", "slow", "latency"],
                sentiment=sent,
                topic="outage",
            )
            db.add(e)
            created.append(e)
        # KPI degradation
        # Fetch latest KPI to base from
        latest = (
            db.query(KPI)
            .filter(KPI.region == region)
            .order_by(KPI.ts.desc())
            .first()
        )
        if latest:
            degraded = KPI(
                ts=ts,
                region=region,
                download_mbps=max(0.1, latest.download_mbps * (1.0 - impact_percent / 100.0)),
                latency_ms=latest.latency_ms * (1.0 + impact_percent / 100.0),
            )
            db.add(degraded)
    db.commit()
    return created


