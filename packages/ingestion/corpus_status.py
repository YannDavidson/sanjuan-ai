"""Corpus readiness reporting for SanJuan AI.

This helper summarizes whether the local document corpus is ready for retrieval.
It is used by `/health` and `/ask` so the API can be honest when raw documents,
chunks, or vector artifacts have not been generated yet.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from packages.ingestion.batch_ingest_sources import DEFAULT_OUTPUT_DIR as DEFAULT_RAW_DIR
from packages.retrieval.chunk_documents import DEFAULT_OUTPUT_DIR as DEFAULT_CHUNKS_DIR
from packages.retrieval.local_vector_search import DEFAULT_VECTORS_DIR

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CorpusStatus:
    """High-level local corpus readiness status."""

    ready_for_keyword_retrieval: bool
    ready_for_vector_retrieval: bool
    raw_documents_count: int
    chunk_files_count: int
    chunks_count: int
    vector_files_count: int
    vectors_count: int
    warnings: list[str] = field(default_factory=list)
    raw_dir: str = "data/documents/raw"
    chunks_dir: str = "data/documents/chunks"
    vectors_dir: str = "data/documents/vectors"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _count_json_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.json")))


def _count_chunks(chunks_dir: Path) -> int:
    if not chunks_dir.exists():
        return 0

    count = 0
    for path in chunks_dir.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        count += len([chunk for chunk in payload.get("chunks", []) if isinstance(chunk, dict)])
    return count


def _count_vectors(vectors_dir: Path) -> int:
    if not vectors_dir.exists():
        return 0

    count = 0
    for path in vectors_dir.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        count += len([record for record in payload.get("embeddings", []) if isinstance(record, dict)])
    return count


def build_corpus_status(
    raw_dir: Path = DEFAULT_RAW_DIR,
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    vectors_dir: Path = DEFAULT_VECTORS_DIR,
) -> CorpusStatus:
    """Build a corpus status summary from local artifact directories."""
    raw_documents_count = _count_json_files(raw_dir)
    chunk_files_count = _count_json_files(chunks_dir)
    chunks_count = _count_chunks(chunks_dir)
    vector_files_count = _count_json_files(vectors_dir)
    vectors_count = _count_vectors(vectors_dir)

    warnings: list[str] = []
    if raw_documents_count == 0:
        warnings.append("No raw ingested documents found. Run `python -m packages.ingestion.batch_ingest_sources --pretty`.")
    if chunks_count == 0:
        warnings.append("No retrieval chunks found. Run `python -m packages.retrieval.chunk_documents --pretty`.")
    if vectors_count == 0:
        warnings.append("No vector artifacts found. Hybrid retrieval will use keyword-only fallback until vectors are built.")

    return CorpusStatus(
        ready_for_keyword_retrieval=chunks_count > 0,
        ready_for_vector_retrieval=vectors_count > 0,
        raw_documents_count=raw_documents_count,
        chunk_files_count=chunk_files_count,
        chunks_count=chunks_count,
        vector_files_count=vector_files_count,
        vectors_count=vectors_count,
        warnings=warnings,
        raw_dir=_relative(raw_dir),
        chunks_dir=_relative(chunks_dir),
        vectors_dir=_relative(vectors_dir),
    )


def build_corpus_status_dict(
    raw_dir: Path = DEFAULT_RAW_DIR,
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    vectors_dir: Path = DEFAULT_VECTORS_DIR,
) -> dict[str, Any]:
    """Return corpus readiness as a JSON-serializable dictionary."""
    return build_corpus_status(raw_dir=raw_dir, chunks_dir=chunks_dir, vectors_dir=vectors_dir).to_dict()
