#!/usr/bin/env python3
"""
Update CHI scores from tmobile_reviews.jsonl file.
This script:
1. Upserts reviews to Pinecone (t-mobile index)
2. Inserts reviews as Events into SQL database
3. Recomputes CHI scores for all regions
4. Generates alerts for regions with CHI drops
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database import get_db, init_db, SessionLocal
from backend.models import Event
from backend.chi import recompute_and_store_chi
from backend.alerts import generate_alerts_for_regions
from backend.utils import clean_text, compute_sentiment, extract_keywords_texts, classify_topic_from_keywords

# Import Pinecone functions
try:
    from ingest_to_pinecone_e5 import get_index, embed_passages, upsert_batch
    PINECONE_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Pinecone not available: {e}")
    PINECONE_AVAILABLE = False


def load_reviews(jsonl_path: str) -> List[Dict[str, Any]]:
    """Load reviews from JSONL file."""
    path = Path(jsonl_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if isinstance(rec, dict) and "text" in rec:
                    records.append(rec)
            except json.JSONDecodeError as e:
                print(f"[WARNING] Skipping invalid JSON on line {line_num}: {e}")
                continue
    
    print(f"[INFO] Loaded {len(records)} reviews from {path}")
    return records


def upsert_to_pinecone(records: List[Dict[str, Any]]) -> int:
    """Upsert reviews to Pinecone."""
    if not PINECONE_AVAILABLE:
        print("[WARNING] Pinecone not available, skipping vector upsert")
        return 0
    
    try:
        index, namespace = get_index()
        index_name = os.getenv("PINECONE_INDEX", "t-mobile")
        print(f"[INFO] Upserting to Pinecone index: {index_name}, namespace: {namespace}")
        
        # Load embedding model
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDINGS_MODEL", "intfloat/multilingual-e5-large")
        print(f"[INFO] Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        
        # Prepare batches
        batch_size = 10
        total_upserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            print(f"[INFO] Processing batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}")
            upsert_batch(index, namespace, model, batch)
            total_upserted += len(batch)
        
        print(f"[INFO] Successfully upserted {total_upserted} reviews to Pinecone")
        return total_upserted
    except Exception as e:
        print(f"[ERROR] Failed to upsert to Pinecone: {e}")
        import traceback
        traceback.print_exc()
        return 0


def insert_to_database(records: List[Dict[str, Any]]) -> List[str]:
    """Insert reviews as Events into database and return list of regions."""
    db = SessionLocal()
    try:
        regions_changed = []
        
        for rec in records:
            meta = rec.get("metadata", {})
            region = meta.get("region", "Unknown")
            # Extract city name if region has state (e.g., "Atlanta, GA" -> "Atlanta")
            if "," in region:
                region = region.split(",")[0].strip()
            
            text_clean = clean_text(rec.get("text", ""))
            if not text_clean:
                continue
            
            sentiment = compute_sentiment(text_clean)
            keywords_list = extract_keywords_texts([text_clean], top_k=5)
            keywords = keywords_list[0] if keywords_list else []
            topic = classify_topic_from_keywords(keywords)
            
            # Parse timestamp from metadata if available
            ts = datetime.utcnow()
            if "created_at" in meta:
                try:
                    from dateutil.parser import parse
                    ts = parse(meta["created_at"])
                except:
                    pass
            
            e = Event(
                ts=ts,
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
        print(f"[INFO] Inserted {len(records)} events into database")
        print(f"[INFO] Regions affected: {', '.join(regions_changed)}")
        return regions_changed
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to insert to database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def update_chi_scores(regions: List[str]):
    """Recompute CHI scores for all affected regions."""
    db = next(get_db())
    try:
        print(f"[INFO] Recomputing CHI scores for {len(regions)} regions...")
        chi_rows = recompute_and_store_chi(db, regions)
        print(f"[INFO] Created {len(chi_rows)} new CHI records")
        
        # Generate alerts
        print(f"[INFO] Generating alerts for regions...")
        alerts = generate_alerts_for_regions(db, regions)
        print(f"[INFO] Generated {len(alerts)} alerts")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update CHI scores: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def main():
    """Main function to update CHI from reviews."""
    # Get path to reviews file
    reviews_path = os.getenv("REVIEWS_JSONL_PATH", "tmobile_reviews.jsonl")
    if not Path(reviews_path).exists():
        # Try in project root
        reviews_path = project_root / "tmobile_reviews.jsonl"
        if not reviews_path.exists():
            print(f"[ERROR] Reviews file not found. Please provide path to tmobile_reviews.jsonl")
            sys.exit(1)
    
    print(f"[INFO] Starting CHI update from reviews file: {reviews_path}")
    print(f"[INFO] Pinecone index: {os.getenv('PINECONE_INDEX', 't-mobile')}")
    print(f"[INFO] Pinecone namespace: {os.getenv('PINECONE_NAMESPACE', 'default')}")
    
    # Initialize database
    init_db()
    
    # Step 1: Load reviews
    records = load_reviews(str(reviews_path))
    if not records:
        print("[ERROR] No reviews found in file")
        sys.exit(1)
    
    # Step 2: Upsert to Pinecone
    if PINECONE_AVAILABLE:
        upserted = upsert_to_pinecone(records)
        print(f"[INFO] ✅ Upserted {upserted} reviews to Pinecone")
    else:
        print("[WARNING] Skipping Pinecone upsert (not available)")
    
    # Step 3: Insert to database
    regions = insert_to_database(records)
    print(f"[INFO] ✅ Inserted reviews into database")
    
    # Step 4: Update CHI scores
    if regions:
        update_chi_scores(regions)
        print(f"[INFO] ✅ Updated CHI scores for regions: {', '.join(regions)}")
    else:
        print("[WARNING] No regions found in reviews")
    
    print("\n[SUCCESS] CHI update complete!")
    print(f"  - Reviews processed: {len(records)}")
    print(f"  - Regions updated: {len(regions)}")
    if PINECONE_AVAILABLE:
        print(f"  - Pinecone vectors: {upserted}")


if __name__ == "__main__":
    main()

