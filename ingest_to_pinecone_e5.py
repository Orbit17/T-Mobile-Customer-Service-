#!/usr/bin/env python3
"""
Ingest `tmobile_reviews.jsonl` into a Pinecone serverless index configured with
- metric: cosine
- dimensions: 1024
- model: multilingual-e5-large (client-side embedding here)
Requires:
  pip install sentence-transformers pinecone-client==5.*
Env:
  export PINECONE_API_KEY=...
  export PINECONE_INDEX=tmobile-feedback
  export PINECONE_NAMESPACE=default
  # Only needed if index doesn't exist (auto-create):
  export PINECONE_CLOUD=aws
  export PINECONE_REGION=us-east-1
Usage:
  python ingest_to_pinecone_e5.py /path/to/tmobile_reviews.jsonl
"""
import os, sys, json, time
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

BATCH_SIZE = 64

def load_jsonl(path: str) -> List[Dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

def get_index():
    api_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX", "t-mobile")  # Default to t-mobile
    namespace = os.environ.get("PINECONE_NAMESPACE", "default")  # Always use "default"
    if not api_key:
        raise SystemExit("Set PINECONE_API_KEY env var.")
    if not index_name:
        raise SystemExit("Set PINECONE_INDEX env var (or it defaults to 't-mobile').")
    print(f"[DEBUG] Using index: {index_name}, namespace: {namespace}")
    pc = Pinecone(api_key=api_key)
    # Auto-create index if missing
    existing = {idx["name"] for idx in pc.list_indexes()}
    if index_name not in existing:
        cloud = os.environ.get("PINECONE_CLOUD", "aws")
        region = os.environ.get("PINECONE_REGION", "us-east-1")
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    # Return index handle and chosen namespace
    return pc.Index(index_name), namespace

def build_model():
    # intfloat/multilingual-e5-large outputs 1024-d vectors
    # E5 expects 'passage: ' for documents and 'query: ' for queries
    return SentenceTransformer("intfloat/multilingual-e5-large")

def embed_passages(model, texts: List[str]) -> List[List[float]]:
    prefixed = [("passage: " + t) for t in texts]
    # normalize for cosine metric
    return model.encode(prefixed, convert_to_numpy=True, normalize_embeddings=True).tolist()

def upsert_batch(index, namespace: str, model, batch: List[Dict]):
    texts = [r["text"] for r in batch]
    vecs = embed_passages(model, texts)
    pine_vecs = []
    for r, v in zip(batch, vecs):
        # keep original text in metadata for grounded answers
        md = dict(r.get("metadata", {}))
        md["text"] = r["text"]
        # Normalize region name for case-insensitive matching
        if "region" in md:
            # Keep original but also store normalized version
            region_orig = md["region"]
            # Extract city name (before comma if present, e.g., "Atlanta, GA" -> "Atlanta")
            region_city = region_orig.split(",")[0].strip() if "," in region_orig else region_orig.strip()
            md["region"] = region_city  # Store normalized city name
            md["region_original"] = region_orig  # Keep original for reference
        pine_vecs.append({
            "id": r["id"],
            "values": v,
            "metadata": md
        })
    # Ensure namespace is "default" (not empty)
    final_namespace = namespace if namespace else "default"
    print(f"[DEBUG] Upserting {len(pine_vecs)} vectors to namespace='{final_namespace}'")
    index.upsert(vectors=pine_vecs, namespace=final_namespace)

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python ingest_to_pinecone_e5.py /path/to/tmobile_reviews.jsonl")
    path = sys.argv[1]
    data = load_jsonl(path)
    print(f"Loaded {len(data)} docs.")
    index, namespace = get_index()
    print(f"Using namespace='{namespace}'")
    model = build_model()
    for i in range(0, len(data), BATCH_SIZE):
        chunk = data[i:i+BATCH_SIZE]
        upsert_batch(index, namespace, model, chunk)
        print(f"Upserted {i+len(chunk)}/{len(data)}")
        time.sleep(0.1)  # be gentle
    print("Done.")

if __name__ == "__main__":
    main()
