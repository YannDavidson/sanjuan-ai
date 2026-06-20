"""Local deterministic vector search for SanJuan AI chunks.

This module provides an embedding-ready retrieval interface without external API
keys. It uses hashed bag-of-words vectors as a development scaffold. It is not a
replacement for true language-model embeddings, but it lets the project design,
test, and ship the vector retrieval contract before a provider is selected.

Generate local vectors:

    python -m packages.retrieval.local_vector_search build --pretty

Search local vectors:

    python -m packages.retrieval.local_vector_search search "business registration Puerto Rico" --pretty
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from packages.retrieval.keyword_search import DEFAULT_CHUNKS_DIR, RetrievalFilters, matches_filters, tokenize
from packages.shared.embedding_schema import EmbeddingRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VECTORS_DIR = REPO_ROOT / "data" / "documents" / "vectors"
DEFAULT_DIMENSIONS = 384
LOCAL_HASH_MODEL = "hashing-vector-v1"


def hash_token(token: str, dimensions: int) -> int:
    """Map a token to a stable vector dimension."""
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % dimensions


def embed_text_local(text: str, dimensions: int = DEFAULT_DIMENSIONS) -> list[float]:
    """Create a deterministic normalized hashed vector for text."""
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dimensions

    counts = Counter(tokens)
    vector = [0.0] * dimensions
    for token, count in counts.items():
        index = hash_token(token, dimensions)
        # Log-scaled term frequency keeps repeated boilerplate from dominating.
        vector[index] += 1.0 + math.log(count)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector

    return [round(value / norm, 8) for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for normalized or non-normalized vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (left_norm * right_norm)


def load_chunk_files(chunks_dir: Path = DEFAULT_CHUNKS_DIR) -> list[dict[str, Any]]:
    """Load chunk payloads grouped by document from chunk JSON files."""
    if not chunks_dir.exists():
        return []

    payloads: list[dict[str, Any]] = []
    for path in sorted(chunks_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        payload["_input_path"] = str(path)
        payloads.append(payload)

    return payloads


def build_embedding_record(chunk: dict[str, Any], dimensions: int = DEFAULT_DIMENSIONS) -> EmbeddingRecord:
    """Create a local embedding record from one retrieval chunk."""
    chunk_id = str(chunk.get("chunk_id") or "unknown-chunk")
    vector = embed_text_local(str(chunk.get("text") or ""), dimensions=dimensions)
    embedding_id = f"{chunk_id}:embedding:local_hash:{LOCAL_HASH_MODEL}:{dimensions}"
    citation = chunk.get("citation") or {}

    return EmbeddingRecord(
        embedding_id=embedding_id,
        chunk_id=chunk_id,
        document_id=str(chunk.get("document_id") or "unknown-document"),
        source_id=str(chunk.get("source_id") or "unknown-source"),
        source_name=chunk.get("source_name"),
        source_url=chunk.get("source_url"),
        title=chunk.get("title"),
        category=chunk.get("category"),
        geography=chunk.get("geography"),
        language=chunk.get("language"),
        trust_level=chunk.get("trust_level"),
        provider="local_hash",
        model=LOCAL_HASH_MODEL,
        dimensions=dimensions,
        vector=vector,
        content_hash=chunk.get("content_hash"),
        citation=citation,
        metadata={
            "chunk_index": chunk.get("chunk_index"),
            "character_count": chunk.get("character_count"),
            "fetched_at": chunk.get("fetched_at"),
            "source_type": chunk.get("source_type"),
        },
    )


def build_vector_store(
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    vectors_dir: Path = DEFAULT_VECTORS_DIR,
    dimensions: int = DEFAULT_DIMENSIONS,
    pretty: bool = False,
) -> dict[str, Any]:
    """Build local vector JSON files from chunk files."""
    payloads = load_chunk_files(chunks_dir)
    vectors_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    total_vectors = 0

    for payload in payloads:
        document_id = str(payload.get("document_id") or "unknown-document")
        chunks = [chunk for chunk in payload.get("chunks", []) if isinstance(chunk, dict)]
        records = [build_embedding_record(chunk, dimensions=dimensions).model_dump(mode="json") for chunk in chunks]
        output_path = vectors_dir / f"{document_id}.vectors.json"
        indent = 2 if pretty else None
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "document_id": document_id,
                    "provider": "local_hash",
                    "model": LOCAL_HASH_MODEL,
                    "dimensions": dimensions,
                    "embeddings": records,
                },
                file,
                ensure_ascii=False,
                indent=indent,
            )
            file.write("\n")

        total_vectors += len(records)
        results.append(
            {
                "document_id": document_id,
                "status": "vectorized" if records else "skipped",
                "vector_count": len(records),
                "output_path": str(output_path.relative_to(REPO_ROOT)),
            }
        )

    return {
        "chunks_dir": str(chunks_dir.relative_to(REPO_ROOT)) if chunks_dir.is_relative_to(REPO_ROOT) else str(chunks_dir),
        "vectors_dir": str(vectors_dir.relative_to(REPO_ROOT)) if vectors_dir.is_relative_to(REPO_ROOT) else str(vectors_dir),
        "documents_seen": len(payloads),
        "documents_vectorized": len([result for result in results if result["status"] == "vectorized"]),
        "total_vectors": total_vectors,
        "provider": "local_hash",
        "model": LOCAL_HASH_MODEL,
        "dimensions": dimensions,
        "results": results,
    }


def load_vector_records(vectors_dir: Path = DEFAULT_VECTORS_DIR) -> list[dict[str, Any]]:
    """Load local vector records from JSON files."""
    if not vectors_dir.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(vectors_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        for record in payload.get("embeddings", []):
            if isinstance(record, dict):
                record["_vector_file"] = str(path)
                records.append(record)

    return records


def record_matches_filters(record: dict[str, Any], filters: RetrievalFilters | None) -> bool:
    """Reuse retrieval filters for vector records."""
    if filters is None:
        return True
    return matches_filters(record, filters)


def build_vector_result(record: dict[str, Any], score: float) -> dict[str, Any]:
    """Build an API-friendly vector search result."""
    citation = record.get("citation") or {}
    return {
        "embedding_id": record.get("embedding_id"),
        "chunk_id": record.get("chunk_id"),
        "document_id": record.get("document_id"),
        "score": round(score, 6),
        "source_id": record.get("source_id"),
        "source_name": record.get("source_name"),
        "source_url": record.get("source_url"),
        "title": record.get("title"),
        "category": record.get("category"),
        "geography": record.get("geography"),
        "language": record.get("language"),
        "trust_level": record.get("trust_level"),
        "provider": record.get("provider"),
        "model": record.get("model"),
        "citation": {
            "title": citation.get("title") or record.get("title"),
            "url": citation.get("url") or record.get("source_url"),
            "source_id": citation.get("source_id") or record.get("source_id"),
            "source_name": citation.get("source_name") or record.get("source_name"),
        },
    }


def search_vectors(
    query: str,
    vectors_dir: Path = DEFAULT_VECTORS_DIR,
    filters: RetrievalFilters | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search local vector records with cosine similarity."""
    query = query.strip()
    if not query:
        return []

    records = load_vector_records(vectors_dir)
    if not records:
        return []

    dimensions = int(records[0].get("dimensions") or DEFAULT_DIMENSIONS)
    query_vector = embed_text_local(query, dimensions=dimensions)
    scored: list[dict[str, Any]] = []

    for record in records:
        if not record_matches_filters(record, filters):
            continue
        vector = record.get("vector") or []
        score = cosine_similarity(query_vector, vector)
        if score <= 0:
            continue
        scored.append(build_vector_result(record, score=score))

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: max(limit, 0)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or search local SanJuan AI vectors.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build local vector files from chunk files.")
    build_parser.add_argument("--chunks-dir", default=str(DEFAULT_CHUNKS_DIR), help="Directory containing chunk JSON files.")
    build_parser.add_argument("--vectors-dir", default=str(DEFAULT_VECTORS_DIR), help="Directory to write vector JSON files.")
    build_parser.add_argument("--dimensions", type=int, default=DEFAULT_DIMENSIONS, help="Hash vector dimensions.")
    build_parser.add_argument("--pretty", action="store_true", help="Pretty-print vector JSON files and summary.")

    search_parser = subparsers.add_parser("search", help="Search local vector files.")
    search_parser.add_argument("query", help="Search query.")
    search_parser.add_argument("--vectors-dir", default=str(DEFAULT_VECTORS_DIR), help="Directory containing vector JSON files.")
    search_parser.add_argument("--category", default=None, help="Optional category filter.")
    search_parser.add_argument("--trust-level", default=None, help="Optional trust level filter.")
    search_parser.add_argument("--geography", default=None, help="Optional geography filter.")
    search_parser.add_argument("--language", default=None, help="Optional language filter.")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum results.")
    search_parser.add_argument("--pretty", action="store_true", help="Pretty-print search results.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build":
        summary = build_vector_store(
            chunks_dir=Path(args.chunks_dir),
            vectors_dir=Path(args.vectors_dir),
            dimensions=args.dimensions,
            pretty=args.pretty,
        )
        indent = 2 if args.pretty else None
        print(json.dumps(summary, ensure_ascii=False, indent=indent))
        return 0

    filters = RetrievalFilters(
        category=args.category,
        trust_level=args.trust_level,
        geography=args.geography,
        language=args.language,
    )
    results = search_vectors(
        query=args.query,
        vectors_dir=Path(args.vectors_dir),
        filters=filters,
        limit=args.limit,
    )
    payload = {
        "query": args.query,
        "vectors_dir": args.vectors_dir,
        "count": len(results),
        "results": results,
    }
    indent = 2 if args.pretty else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
