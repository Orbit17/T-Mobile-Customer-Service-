from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import init_db, SessionLocal
from .models import Source, Event, KPI, Runbook
from .utils import clean_text, compute_sentiment, extract_keywords_texts


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def ensure_sources(db: Session) -> None:
    names = ["twitter", "reddit", "appstore", "gplay", "survey"]
    existing = {s.name for s in db.scalars(select(Source)).all()}
    for name in names:
        if name not in existing:
            db.add(Source(name=name, meta=None))
    db.commit()


def _source_id(db: Session, name: str) -> Optional[int]:
    row = db.scalars(select(Source).where(Source.name == name)).first()
    return row.id if row else None


def seed_events(db: Session) -> int:
    csv = DATA_DIR / "events_seed.csv"
    if not csv.exists():
        return 0
    # Read only expected columns to avoid trailing-comma extra columns
    df = pd.read_csv(csv, usecols=["ts", "region", "source", "text", "rating"])
    # Clean text and compute features
    df["text_clean"] = df["text"].astype(str).apply(clean_text)
    sentiments = df["text_clean"].apply(compute_sentiment).tolist()
    keywords_batch = extract_keywords_texts(df["text_clean"].tolist(), top_k=5)
    created = 0
    for (_, row), sent, kws in zip(df.iterrows(), sentiments, keywords_batch):
        # Robust timestamp parsing; skip bad rows
        try:
            ts = pd.to_datetime(row["ts"], utc=False).to_pydatetime()
        except Exception:
            continue
        db.add(
            Event(
                ts=ts,
                region=row["region"],
                source_id=_source_id(db, str(row["source"])),
                text=row["text_clean"],
                rating=float(row["rating"]) if not pd.isna(row.get("rating", None)) else None,
                keywords=kws,
                sentiment=float(sent),
                topic=None,  # classified later if needed
            )
        )
        created += 1
    if created:
        db.commit()
    return created


def seed_kpis(db: Session) -> int:
    csv = DATA_DIR / "kpis_seed.csv"
    if not csv.exists():
        return 0
    df = pd.read_csv(csv)
    created = 0
    for _, row in df.iterrows():
        db.add(
            KPI(
                ts=datetime.fromisoformat(row["ts"]),
                region=row["region"],
                download_mbps=float(row["download_mbps"]),
                latency_ms=float(row["latency_ms"]),
            )
        )
        created += 1
    if created:
        db.commit()
    return created


def seed_runbook(db: Session) -> int:
    import json

    f = DATA_DIR / "runbook.json"
    if not f.exists():
        return 0
    items = json.loads(f.read_text())
    # Idempotent insert: skip existing issues (Runbook.issue is unique)
    existing_issues = set(db.scalars(select(Runbook.issue)).all())
    created = 0
    for item in items:
        issue = item["issue"]
        if issue in existing_issues:
            continue
        db.add(Runbook(issue=issue, steps=item["steps"]))
        created += 1
    if created:
        db.commit()
    return created


def main(seed: bool) -> None:
    init_db()
    with SessionLocal() as db:
        ensure_sources(db)
        if seed:
            seed_events(db)
            seed_kpis(db)
            seed_runbook(db)
    print("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="Load seed CSV data")
    args = parser.parse_args()
    main(seed=args.seed)


