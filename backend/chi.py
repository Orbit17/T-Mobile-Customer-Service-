from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from .models import Event, KPI, CHI
from .utils import topic_severity


def _normalize_kpi(download_mbps: float, latency_ms: float) -> float:
    """
    Returns KPI health K in [0,1], where 0.5 is neutral.
    Download: >=100 is great (~1.0), <=5 is poor (~0.0)
    Latency: <=30 is great (~1.0), >=200 is poor (~0.0)
    """
    # Normalize download
    dl = np.clip((download_mbps - 5.0) / (100.0 - 5.0), 0.0, 1.0)
    # Normalize latency (lower is better)
    lt = 1.0 - np.clip((latency_ms - 30.0) / (200.0 - 30.0), 0.0, 1.0)
    return float((dl + lt) / 2.0)


def _volume_zscore(db: Session, region: str, window: timedelta) -> float:
    """
    Compute z-score for event volume in the given window vs the last 24h baseline for the region.
    """
    now = datetime.utcnow()
    start = now - window
    past_24h = now - timedelta(hours=24)

    # Current volume in window
    current_count = db.scalar(
        select(func.count()).select_from(Event).where(
            Event.region == region,
            Event.ts >= start,
            Event.ts <= now,
        )
    ) or 0

    # Compute hourly volumes in the past 24h (excluding current window)
    hourly_counts: List[int] = []
    t = past_24h
    while t < now - window:
        t_end = t + window
        cnt = db.scalar(
            select(func.count()).select_from(Event).where(
                Event.region == region,
                Event.ts >= t,
                Event.ts < t_end,
            )
        ) or 0
        hourly_counts.append(int(cnt))
        t = t_end

    if len(hourly_counts) == 0:
        return 0.0
    mean = float(np.mean(hourly_counts))
    std = float(np.std(hourly_counts))
    if std == 0:
        return 0.0
    return float((current_count - mean) / std)


def _compute_topic_severity(events: List[Event]) -> float:
    if not events:
        return 0.0
    # Weighted by negative events; scale to 0..1
    severities = [topic_severity(e.topic or "other") for e in events if (e.sentiment or 0) < 0]
    if not severities:
        return 0.0
    return float(np.clip(np.mean(severities), 0.0, 1.0))


def _kudos_count(events: List[Event]) -> int:
    return int(sum(1 for e in events if (e.sentiment or 0) > 0.6))


def compute_chi_for_region(db: Session, region: str, window_minutes: int = 15) -> Tuple[float, dict]:
    """
    Compute CHI for a single region using the last `window_minutes`.
    Returns (chi_score, drivers_json)
    """
    now = datetime.utcnow()
    start = now - timedelta(minutes=window_minutes)
    events: List[Event] = list(
        db.scalars(
            select(Event)
            .where(Event.region == region, Event.ts >= start, Event.ts <= now)
            .order_by(Event.ts)
        )
    )

    # Sentiment S (weighted by volume)
    sentiments = [e.sentiment for e in events if e.sentiment is not None]
    S = float(np.mean(sentiments)) if sentiments else 0.0

    # Volume factor V (not directly used in formula; used via zscore)
    # Compute KPI health K from latest KPI
    kpi = db.scalars(
        select(KPI)
        .where(KPI.region == region)
        .order_by(desc(KPI.ts))
        .limit(1)
    ).first()
    if kpi is None:
        K = 0.5  # neutral if unknown
    else:
        K = _normalize_kpi(kpi.download_mbps, kpi.latency_ms)

    # Topic severity T
    T = _compute_topic_severity(events)

    # Kudos boost
    kudos = _kudos_count(events)

    # Spike penalty from z-score
    z = _volume_zscore(db, region, timedelta(minutes=window_minutes))

    base = 50.0 + 50.0 * (0.55 * S + 0.25 * (K - 0.5) * 2.0 + 0.20 * (1.0 - T))
    boost = min(10.0, 5.0 * kudos)
    spike_penalty = min(15.0, max(0.0, z) * 5.0)
    chi_score = float(np.clip(base + boost - spike_penalty, 0.0, 100.0))

    # Drivers: top keywords, KPI health, topic severity
    # Aggregate top keywords frequency
    kw_freq: Dict[str, int] = defaultdict(int)
    for e in events:
        for k in (e.keywords or []):
            kw_freq[str(k).lower()] += 1
    top_keywords = sorted(kw_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    drivers = {
        "top_keywords": [k for k, _ in top_keywords],
        "kpi_health": K,
        "topic_severity": T,
        "volume_z": z,
        "kudos": kudos,
        "sentiment": S,
    }
    return chi_score, drivers


def recompute_and_store_chi(db: Session, regions: List[str], window_minutes: int = 15) -> List[CHI]:
    """
    Recompute CHI for the given regions and store a new row for each region.
    Returns created CHI rows.
    """
    now = datetime.utcnow()
    created: List[CHI] = []
    for region in regions:
        score, drivers = compute_chi_for_region(db, region, window_minutes=window_minutes)
        row = CHI(ts=now, region=region, score=score, drivers_json=drivers)
        db.add(row)
        created.append(row)
    db.commit()
    return created


