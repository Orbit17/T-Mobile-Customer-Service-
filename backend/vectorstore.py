from __future__ import annotations
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple

# Load environment variables early
try:
    from dotenv import load_dotenv
    import pathlib
    # Try loading from project root (one level up from backend/)
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    # Also try current directory
    load_dotenv(override=False)
except ImportError:
    pass  # dotenv not available, rely on system env vars

from sentence_transformers import SentenceTransformer

try:
    # Modern Pinecone SDK
    from pinecone import Pinecone, ServerlessSpec
except ImportError as e:
    # Log the actual import error for debugging
    import sys
    print(f"[WARNING] Failed to import Pinecone: {e}", file=sys.stderr)
    Pinecone = None  # type: ignore
    ServerlessSpec = None  # type: ignore
except Exception as e:
    # Log other exceptions too
    import sys
    print(f"[WARNING] Unexpected error importing Pinecone: {e}", file=sys.stderr)
    Pinecone = None  # type: ignore
    ServerlessSpec = None  # type: ignore

_embedder: Optional[SentenceTransformer] = None
_pc: Optional[Any] = None
_index: Optional[Any] = None
_dim: Optional[int] = None


def _load_embedder() -> SentenceTransformer:
    global _embedder, _dim
    if _embedder is None:
        # Default to 1024-dim multilingual model to match common Pinecone presets
        model_name = os.getenv("EMBEDDINGS_MODEL", "intfloat/multilingual-e5-large")
        _embedder = SentenceTransformer(model_name)
        # all-MiniLM-L6-v2 output dimension is 384
        try:
            test_vec = _embedder.encode(["dim_check"], normalize_embeddings=True)
            _dim = int(test_vec.shape[1])
        except Exception:
            # Fallback to the common dim for e5-large
            _dim = 1024
    return _embedder


def _get_pinecone() -> Any:
    global _pc
    if _pc is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "PINECONE_API_KEY not set. Please set it in your .env file or export it:\n"
                "  export PINECONE_API_KEY=your_key_here\n"
                "Or add it to a .env file in the project root."
            )
        if Pinecone is None:
            raise RuntimeError("Pinecone SDK not installed. Run: pip install pinecone")
        _pc = Pinecone(api_key=api_key)
    return _pc


def _get_index() -> Any:
    global _index, _dim
    if _index is not None:
        return _index
    pc = _get_pinecone()
    _load_embedder()
    assert _dim is not None
    index_name = os.getenv("PINECONE_INDEX", "t-mobile")
    existing = {idx["name"] for idx in pc.list_indexes()}
    if index_name not in existing:
        cloud = os.getenv("PINECONE_CLOUD", "aws")
        region = os.getenv("PINECONE_REGION", "us-east-1")
        pc.create_index(
            name=index_name,
            dimension=_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    host = os.getenv("PINECONE_HOST")
    # If host is provided, pin to that host to avoid discovery mismatch
    _index = pc.Index(index_name, host=host) if host else pc.Index(index_name)
    return _index


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def upsert_texts(texts: List[str], namespace: str = "default", metadata: Optional[Dict[str, Any]] = None) -> int:
    if not texts:
        return 0
    embedder = _load_embedder()
    index = _get_index()
    vectors = embedder.encode(texts, normalize_embeddings=True)
    items = []
    for i, vec in enumerate(vectors):
        meta = {"text": texts[i]}
        if metadata:
            meta.update(metadata)
        items.append(
            {
                "id": str(uuid.uuid4()),
                "values": vec.tolist(),
                "metadata": meta,
            }
        )
    index.upsert(vectors=items, namespace=namespace)
    return len(items)


def query_text(query: str, top_k: int = 8, namespace: str = "default", region_filter: Optional[str] = None, issue_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Query Pinecone with optional region and issue_type filtering.
    If filters are provided and return 0 results, falls back to unfiltered query.
    """
    if not (query or "").strip():
        return []
    
    embedder = _load_embedder()
    index = _get_index()
    index_name = os.getenv("PINECONE_INDEX", "t-mobile")
    
    # E5 models expect "query: " prefix for queries
    model_name = os.getenv("EMBEDDINGS_MODEL", "intfloat/multilingual-e5-large")
    if "e5" in model_name.lower():
        query_prefixed = "query: " + query
    else:
        query_prefixed = query
    
    qv = embedder.encode([query_prefixed], normalize_embeddings=True)[0].tolist()
    
    # Debug logging
    print(f"[DEBUG] Pinecone query: index={index_name}, namespace={namespace}, top_k={top_k}, region_filter={region_filter}, issue_type_filter={issue_type_filter}")
    print(f"[DEBUG] Embedding model: {model_name}, dimension: {len(qv)}")
    
    # Build filter dict if we have filters
    filter_dict = None
    if region_filter or issue_type_filter:
        filter_parts = []
        if region_filter:
            filter_parts.append({"region": {"$eq": region_filter}})
        if issue_type_filter:
            filter_parts.append({"issue_type": {"$eq": issue_type_filter}})
        if len(filter_parts) == 1:
            filter_dict = filter_parts[0]
        elif len(filter_parts) == 2:
            # Combine with AND
            filter_dict = {"$and": filter_parts}
    
    # Try with filters if provided
    if filter_dict:
        try:
            res = index.query(
                namespace=namespace,
                vector=qv,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict,
            )
            matches = getattr(res, "matches", []) or []
            filter_desc = f"region={region_filter}" if region_filter else ""
            if issue_type_filter:
                filter_desc += f", issue_type={issue_type_filter}" if filter_desc else f"issue_type={issue_type_filter}"
            print(f"[DEBUG] Filtered query ({filter_desc}) returned {len(matches)} matches")
            
            # If filtered query returns results, use them
            if matches:
                out = []
                for m in matches:
                    meta = getattr(m, "metadata", {}) or {}
                    # Validate region match if region_filter was provided
                    if region_filter:
                        meta_region = (meta.get("region") or "").lower().strip()
                        meta_region_city = meta_region.split(",")[0].strip()
                        region_filter_lower = region_filter.lower().strip()
                        if meta_region_city != region_filter_lower and meta_region != region_filter_lower:
                            continue  # Skip if region doesn't match
                    out.append({
                        "id": getattr(m, "id", None),
                        "score": getattr(m, "score", 0.0),
                        "text": meta.get("text", ""),
                        "metadata": meta,
                    })
                if out:
                    print(f"[DEBUG] Using {len(out)} filtered results")
                    return out
            # Fallback to unfiltered if filtered returns 0
            print(f"[DEBUG] Filtered query returned 0 results, falling back to unfiltered query")
        except Exception as e:
            print(f"[DEBUG] Filter error: {e}, falling back to unfiltered query")
    
    # Unfiltered query (or fallback)
    res = index.query(
        namespace=namespace,
        vector=qv,
        top_k=top_k,
        include_metadata=True,
    )
    matches = getattr(res, "matches", []) or []
    print(f"[DEBUG] Unfiltered query returned {len(matches)} matches")
    
    out: List[Dict[str, Any]] = []
    for m in matches:
        meta = getattr(m, "metadata", {}) or {}
        # No score threshold - return all matches
        out.append(
            {
                "id": getattr(m, "id", None),
                "score": getattr(m, "score", 0.0),
                "text": meta.get("text", ""),
                "metadata": meta,
            }
        )
    
    print(f"[DEBUG] Returning {len(out)} results")
    return out


def upsert_items(items_in: List[Dict[str, Any]], namespace: str = "default") -> int:
    """
    Upsert items with per-document metadata.
    items_in: [{text: str, metadata: {...}, id?: str}]
    Normalizes region names for case-insensitive matching.
    """
    if not items_in:
        return 0
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    ids: List[Optional[str]] = []
    for it in items_in:
        text = (it.get("text") or "").strip()
        if not text:
            continue
        texts.append(text)
        # Normalize region in metadata
        meta = dict(it.get("metadata") or {})
        if "region" in meta:
            region_orig = meta["region"]
            # Extract city name (before comma if present, e.g., "Atlanta, GA" -> "Atlanta")
            region_city = region_orig.split(",")[0].strip() if "," in str(region_orig) else str(region_orig).strip()
            meta["region"] = region_city  # Store normalized city name
            meta["region_original"] = region_orig  # Keep original for reference
        metas.append(meta)
        ids.append(it.get("id"))
    if not texts:
        return 0
    embedder = _load_embedder()
    index = _get_index()
    # Use "passage: " prefix for E5 models (same as ingestion script)
    model_name = os.getenv("EMBEDDINGS_MODEL", "intfloat/multilingual-e5-large")
    if "e5" in model_name.lower():
        prefixed_texts = [("passage: " + t) for t in texts]
        vectors = embedder.encode(prefixed_texts, normalize_embeddings=True)
    else:
        vectors = embedder.encode(texts, normalize_embeddings=True)
    payload = []
    for i, vec in enumerate(vectors):
        meta = {"text": texts[i]}  # Store original text without prefix
        meta.update(metas[i] or {})
        payload.append(
            {
                "id": ids[i] or str(uuid.uuid4()),
                "values": vec.tolist(),
                "metadata": meta,
            }
        )
    # Ensure namespace is "default" (not empty)
    final_namespace = namespace if namespace else "default"
    print(f"[DEBUG] Upserting {len(payload)} vectors to namespace='{final_namespace}'")
    index.upsert(vectors=payload, namespace=final_namespace)
    return len(payload)


