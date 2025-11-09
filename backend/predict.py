from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .models import CHI


def forecast_chi(db: Session, region: str, horizon_minutes: int = 120, step_minutes: int = 15) -> List[Tuple[datetime, float]]:
    """
    Simple linear regression on last N points to forecast next horizon.
    """
    rows = list(
        db.scalars(
            select(CHI).where(CHI.region == region).order_by(desc(CHI.ts)).limit(24)
        )
    )
    if len(rows) < 4:
        # naive persistence
        if rows:
            last = rows[0]
            times = [last.ts + timedelta(minutes=step_minutes * i) for i in range(1, int(horizon_minutes / step_minutes) + 1)]
            return [(t, float(last.score)) for t in times]
        return []

    # Order ascending by time
    rows = list(reversed(rows))
    y = np.array([r.score for r in rows], dtype=float)
    # Time as 0..N-1
    x = np.arange(len(rows), dtype=float)
    x = np.vstack([x, np.ones_like(x)]).T
    # Least squares
    coeff, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    slope, intercept = float(coeff[0]), float(coeff[1])

    last_ts = rows[-1].ts
    num_steps = int(horizon_minutes / step_minutes)
    forecasts: List[Tuple[datetime, float]] = []
    base_idx = len(rows) - 1
    for i in range(1, num_steps + 1):
        t = last_ts + timedelta(minutes=step_minutes * i)
        idx = base_idx + i
        pred = slope * idx + intercept
        forecasts.append((t, float(np.clip(pred, 0.0, 100.0))))
    return forecasts


