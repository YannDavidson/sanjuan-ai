"""Local keyword retrieval over SanJuan AI document chunks.

Run from the repository root after batch ingestion and chunking:

    python -m packages.retrieval.keyword_search "business registration Puerto Rico" --pretty
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHUNKS_DIR = REPO_ROOT / "data" / "documents" / "chunks"
DEFAULT_LIMIT = 5

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "con",
    "de",
    "del",
    "el",
    "en",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "la",
    "las",
    "los",
    "of",
    "or",
    "para",
    "por",
    "que",
    "the",
    "to",
    "un",
    "una",
    "y",
}

TRUST_BOOSTS = {
    "official": 3.0,
    "institutional": 1.5,
    "community": 0.5,
    "experimental": 0.0,
}


@dataclass(frozen=True)
class RetrievalFilters:
    """Optional filters for local chunk retrieval."""

    category: str | None = None
    trust_level: str | None = None
    geography: str | None = None
    language: str | None = None


def normalize(value: str | None) -> str:
    """Normalize text for simple matching."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.lower()).strip()


def tokenize(value: str | None) -> list[str]:
    """Tokenize query or document text for MVP keyword scoring."""
    normalized = normalize(value)
    tokens = re.findall(r"[\wáéíóúüñ]+", normalized, flags=re.IGNORECASE)
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def load_chunks(chunks_dir: Path = DEFAULT_CHUNKS_DIR) -> list[dict[str, Any]]:
    """Load all retrieval chunks from JSON files.

    Returns an empty list if the chunks directory does not exist yet.
    """
    if not chunks_dir.exists():
        return []

    chunks: list[dict[str, Any]] = []
    for path in sorted(chunks_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        for chunk in payload.get("chunks", []):
            if isinstance(chunk, dict):
                chunk["_chunk_file"] = str(path)
                chunks.append(chunk)

    return chunks


def matches_filters(chunk: dict[str, Any], filters: RetrievalFilters | None) -> bool:
    """Return True when a chunk matches all requested filters."""
    if filters is None:
        return True

    if filters.category and chunk.get("category") != filters.category:
        return False
    if filters.trust_level and chunk.get("trust_level") != filters.trust_level:
        return False
    if filters.geography and chunk.get("geography") != filters.geography:
        return False
    if filters.language and chunk.get("language") != filters.language:
        return False

    return True


def score_chunk(query: str, query_tokens: list[str], chunk: dict[str, Any]) -> float:
    """Score a chunk using simple transparent keyword heuristics."""
    if not query_tokens:
        return 0.0

    text = normalize(chunk.get("text"))
    title = normalize(chunk.get("title"))
    source_name = normalize(chunk.get("source_name"))
    category = normalize(chunk.get("category"))
    combined_metadata = f"{title} {source_name} {category}"
    query_normalized = normalize(query)

    text_tokens = tokenize(text)
    text_token_set = set(text_tokens)
    query_token_set = set(query_tokens)
    overlap = query_token_set.intersection(text_token_set)

    if not overlap and query_normalized not in text:
        return 0.0

    score = 0.0

    # Exact phrase match is a strong signal for this MVP search layer.
    if query_normalized and query_normalized in text:
        score += 12.0

    # Token overlap favors chunks covering more of the user's question.
    score += len(overlap) * 4.0
    score += (len(overlap) / max(len(query_token_set), 1)) * 8.0

    # Repeated term frequency gives a mild boost without dominating results.
    for token in overlap:
        score += min(text_tokens.count(token), 5) * 0.4

    # Metadata matches are helpful for pages with broad civic content.
    for token in query_token_set:
        if token in combined_metadata:
            score += 2.0

    # Trust level matters because SanJuan AI should favor official sources.
    score += TRUST_BOOSTS.get(str(chunk.get("trust_level") or ""), 0.0)

    # Slightly prefer shorter chunks when scores are otherwise similar.
    character_count = int(chunk.get("character_count") or len(text) or 1)
    score += 1 / math.sqrt(max(character_count, 1))

    return round(score, 4)


def build_retrieval_result(chunk: dict[str, Any], score: float) -> dict[str, Any]:
    """Build a stable API-friendly retrieval result."""
    citation = chunk.get("citation") or {}
    return {
        "chunk_id": chunk.get("chunk_id"),
        "document_id": chunk.get("document_id"),
        "score": score,
        "text": chunk.get("text"),
        "source_id": chunk.get("source_id"),
        "source_name": chunk.get("source_name"),
        "source_url": chunk.get("source_url"),
        "title": chunk.get("title"),
        "category": chunk.get("category"),
        "geography": chunk.get("geography"),
        "language": chunk.get("language"),
        "trust_level": chunk.get("trust_level"),
        "fetched_at": chunk.get("fetched_at"),
        "content_hash": chunk.get("content_hash"),
        "citation": {
            "title": citation.get("title") or chunk.get("title"),
            "url": citation.get("url") or chunk.get("source_url"),
            "source_id": citation.get("source_id") or chunk.get("source_id"),
            "source_name": citation.get("source_name") or chunk.get("source_name"),
        },
    }


def search_chunks(
    query: str,
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    filters: RetrievalFilters | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Search local chunks and return ranked evidence blocks."""
    query_tokens = tokenize(query)
    if not query.strip() or not query_tokens:
        return []

    scored_results: list[dict[str, Any]] = []
    for chunk in load_chunks(chunks_dir):
        if not matches_filters(chunk, filters):
            continue

        score = score_chunk(query=query, query_tokens=query_tokens, chunk=chunk)
        if score <= 0:
            continue

        scored_results.append(build_retrieval_result(chunk, score=score))

    scored_results.sort(key=lambda item: item["score"], reverse=True)
    return scored_results[: max(limit, 0)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search SanJuan AI local retrieval chunks.")
    parser.add_argument("query", help="Search query.")
    parser.add_argument(
        "--chunks-dir",
        default=str(DEFAULT_CHUNKS_DIR),
        help="Directory containing chunk JSON files.",
    )
    parser.add_argument("--category", default=None, help="Optional category filter.")
    parser.add_argument("--trust-level", default=None, help="Optional trust level filter.")
    parser.add_argument("--geography", default=None, help="Optional geography filter.")
    parser.add_argument("--language", default=None, help="Optional language filter.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximum results. Default: {DEFAULT_LIMIT}")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    filters = RetrievalFilters(
        category=args.category,
        trust_level=args.trust_level,
        geography=args.geography,
        language=args.language,
    )
    results = search_chunks(
        query=args.query,
        chunks_dir=Path(args.chunks_dir),
        filters=filters,
        limit=args.limit,
    )

    payload = {
        "query": args.query,
        "chunks_dir": args.chunks_dir,
        "count": len(results),
        "results": results,
    }
    indent = 2 if args.pretty else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
