#!/usr/bin/env python3
"""
Ingest reviews from JSONL into SQL DB to update CHI.
This complements the Pinecone ingestion.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import init_db, SessionLocal
from backend.models import Event
from backend.utils import clean_text, compute_sentiment, extract_keywords_texts, classify_topic_from_keywords
from backend.chi import recompute_and_store_chi
from backend.alerts import generate_alerts_for_regions

def load_jsonl(path: str):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if isinstance(rec, dict) and "text" in rec:
                    records.append(rec)
            except Exception:
                continue
    return records

def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_reviews_to_db.py /path/to/tmobile_reviews.jsonl")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    records = load_jsonl(jsonl_path)
    print(f"Loaded {len(records)} reviews")
    
    init_db()
    db = SessionLocal()
    
    regions_changed = set()
    
    try:
        for rec in records:
            meta = rec.get("metadata", {})
            # Extract region - handle formats like "Chicago, IL" or just "Chicago"
            region_raw = meta.get("region", "Unknown")
            # For now, use the full region string as-is
            region = region_raw.split(",")[0].strip() if "," in region_raw else region_raw.strip()
            if not region:
                region = "Unknown"
            
            text = rec.get("text", "").strip()
            if not text:
                continue
            
            text_clean = clean_text(text)
            sentiment = compute_sentiment(text_clean)
            keywords_list = extract_keywords_texts([text_clean], top_k=5)
            keywords = keywords_list[0] if keywords_list else []
            topic = classify_topic_from_keywords(keywords)
            
            # Parse timestamp if available
            ts_str = meta.get("created_at")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()
            
            rating = meta.get("rating")
            if rating is not None:
                try:
                    rating = float(rating)
                except Exception:
                    rating = None
            
            e = Event(
                ts=ts,
                region=region,
                source_id=None,
                text=text_clean,
                rating=rating,
                keywords=keywords,
                sentiment=sentiment,
                topic=topic,
            )
            db.add(e)
            regions_changed.add(region)
        
        db.commit()
        print(f"Inserted {len(records)} events into database")
        
        # Recompute CHI for all affected regions
        regions_list = list(regions_changed)
        print(f"Recomputing CHI for regions: {', '.join(regions_list)}")
        recompute_and_store_chi(db, regions_list)
        print("CHI recomputed successfully")
        
        # Generate alerts
        alerts = generate_alerts_for_regions(db, regions_list)
        print(f"Generated {len(alerts)} alerts")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

