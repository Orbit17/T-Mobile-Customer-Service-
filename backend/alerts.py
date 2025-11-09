from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .models import Alert, CHI, KPI


def _latest_chi(db: Session, region: str) -> Optional[CHI]:
    return db.scalars(
        select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(1)
    ).first()


def _previous_chi(db: Session, region: str) -> Optional[CHI]:
    # Get 2nd latest
    rows = list(
        db.scalars(
            select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(2)
        )
    )
    if len(rows) < 2:
        return None
    return rows[1]


def _kpi_drop_25(db: Session, region: str) -> bool:
    # Compare last two KPI snapshots
    rows = list(
        db.scalars(
            select(KPI).where(KPI.region == region).order_by(desc(KPI.ts)).limit(2)
        )
    )
    if len(rows) < 2:
        return False
    latest, prev = rows[0], rows[1]
    if prev.download_mbps > 0 and latest.download_mbps < 0.75 * prev.download_mbps:
        return True
    if prev.latency_ms > 0 and latest.latency_ms > 1.25 * prev.latency_ms:
        return True
    return False


def generate_alerts_for_regions(db: Session, regions: List[str]) -> List[Alert]:
    """
    Based on most recent CHI rows per region, generate alerts if thresholds are met.
    """
    created: List[Alert] = []
    now = datetime.utcnow()
    for region in regions:
        latest = _latest_chi(db, region)
        if latest is None:
            continue
        prev = _previous_chi(db, region)
        chi_before = prev.score if prev else None
        chi_after = latest.score
        drop = (chi_before - chi_after) if (chi_before is not None) else 0.0

        reason_parts: List[str] = []
        if chi_after < 60.0 and drop >= 10.0:
            reason_parts.append("CHI drop ≥10 and <60")
        if (latest.drivers_json or {}).get("volume_z", 0) >= 2.0:
            reason_parts.append("Volume spike ≥2σ")
        if _kpi_drop_25(db, region):
            reason_parts.append("KPI degraded ≥25%")

        if not reason_parts:
            continue

        top_topics = (latest.drivers_json or {}).get("top_keywords", [])[:3]
        recommendation = [
            "Investigate local towers",
            "Notify customers via SMS",
            "Escalate to NOC if persists",
        ]
        alert = Alert(
            ts=now,
            region=region,
            chi_before=chi_before,
            chi_after=chi_after,
            reason=" + ".join(reason_parts) + (f" | topics: {', '.join(top_topics)}" if top_topics else ""),
            recommendation=recommendation,
        )
        db.add(alert)
        created.append(alert)

    if created:
        db.commit()
    return created


