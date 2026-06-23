"""Run the SanJuan AI local corpus refresh pipeline.

This command is the scheduler-friendly wrapper around the existing ingestion and
retrieval preparation steps:

    batch ingest -> source status -> chunk documents -> build local vectors

Run from the repository root:

    python -m packages.ingestion.refresh_corpus --pretty

For CI or documentation dry-runs that should not fetch live websites:

    python -m packages.ingestion.refresh_corpus --dry-run --pretty
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.ingestion.batch_ingest_sources import DEFAULT_OUTPUT_DIR as DEFAULT_RAW_DIR
from packages.ingestion.batch_ingest_sources import ingest_sources
from packages.ingestion.load_sources import DEFAULT_SOURCE_REGISTRY_PATH
from packages.ingestion.source_status import DEFAULT_STATUS_PATH, build_source_status_report, write_status_report
from packages.retrieval.chunk_documents import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_OUTPUT_DIR as DEFAULT_CHUNKS_DIR
from packages.retrieval.chunk_documents import chunk_documents
from packages.retrieval.local_vector_search import DEFAULT_DIMENSIONS, DEFAULT_VECTORS_DIR, build_vector_store

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFRESH_LOG_PATH = REPO_ROOT / "data" / "status" / "last_refresh.json"


def _relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def build_dry_run_summary(
    registry_path: Path,
    raw_dir: Path,
    chunks_dir: Path,
    vectors_dir: Path,
    status_path: Path,
    refresh_log_path: Path,
) -> dict[str, Any]:
    """Return the planned refresh steps without fetching or writing artifacts."""
    return {
        "mode": "dry_run",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [
            "batch_ingest_sources",
            "source_status",
            "chunk_documents",
            "local_vector_search_build",
        ],
        "paths": {
            "registry_path": _relative_or_absolute(registry_path),
            "raw_dir": _relative_or_absolute(raw_dir),
            "chunks_dir": _relative_or_absolute(chunks_dir),
            "vectors_dir": _relative_or_absolute(vectors_dir),
            "status_path": _relative_or_absolute(status_path),
            "refresh_log_path": _relative_or_absolute(refresh_log_path),
        },
        "network_required": True,
        "writes_artifacts": True,
    }


def write_refresh_log(summary: dict[str, Any], output_path: Path, pretty: bool = False) -> Path:
    """Write a refresh summary artifact."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=indent)
        file.write("\n")
    return output_path


def refresh_corpus(
    registry_path: Path = DEFAULT_SOURCE_REGISTRY_PATH,
    raw_dir: Path = DEFAULT_RAW_DIR,
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    vectors_dir: Path = DEFAULT_VECTORS_DIR,
    status_path: Path = DEFAULT_STATUS_PATH,
    refresh_log_path: Path = DEFAULT_REFRESH_LOG_PATH,
    timeout_seconds: int = 20,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    dimensions: int = DEFAULT_DIMENSIONS,
    pretty: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the local refresh pipeline and return a summary."""
    if dry_run:
        return build_dry_run_summary(
            registry_path=registry_path,
            raw_dir=raw_dir,
            chunks_dir=chunks_dir,
            vectors_dir=vectors_dir,
            status_path=status_path,
            refresh_log_path=refresh_log_path,
        )

    started_at = datetime.now(timezone.utc)
    ingest_summary = ingest_sources(
        registry_path=registry_path,
        output_dir=raw_dir,
        timeout_seconds=timeout_seconds,
        pretty=pretty,
    )
    status_report = build_source_status_report(registry_path=registry_path, raw_dir=raw_dir)
    write_status_report(status_report, output_path=status_path, pretty=pretty)
    chunk_summary = chunk_documents(
        input_dir=raw_dir,
        output_dir=chunks_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        pretty=pretty,
    )
    vector_summary = build_vector_store(
        chunks_dir=chunks_dir,
        vectors_dir=vectors_dir,
        dimensions=dimensions,
        pretty=pretty,
    )
    finished_at = datetime.now(timezone.utc)

    summary = {
        "mode": "refresh",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "ingest": ingest_summary,
        "source_status": {
            "total_sources": status_report["total_sources"],
            "by_status": status_report["by_status"],
            "by_priority": status_report["by_priority"],
            "output_path": _relative_or_absolute(status_path),
        },
        "chunking": chunk_summary,
        "vectors": vector_summary,
    }
    write_refresh_log(summary, output_path=refresh_log_path, pretty=pretty)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh the local SanJuan AI corpus artifacts.")
    parser.add_argument("--registry", default=str(DEFAULT_SOURCE_REGISTRY_PATH), help="Path to source registry YAML.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="Directory for raw document artifacts.")
    parser.add_argument("--chunks-dir", default=str(DEFAULT_CHUNKS_DIR), help="Directory for chunk artifacts.")
    parser.add_argument("--vectors-dir", default=str(DEFAULT_VECTORS_DIR), help="Directory for vector artifacts.")
    parser.add_argument("--status-output", default=str(DEFAULT_STATUS_PATH), help="Source status JSON output path.")
    parser.add_argument("--refresh-log", default=str(DEFAULT_REFRESH_LOG_PATH), help="Refresh summary JSON output path.")
    parser.add_argument("--timeout", type=int, default=20, help="Fetch timeout in seconds per source.")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Chunk size in characters.")
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP, help="Chunk overlap in characters.")
    parser.add_argument("--dimensions", type=int, default=DEFAULT_DIMENSIONS, help="Local hash vector dimensions.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned steps without fetching or writing artifacts.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON outputs.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = refresh_corpus(
        registry_path=Path(args.registry),
        raw_dir=Path(args.raw_dir),
        chunks_dir=Path(args.chunks_dir),
        vectors_dir=Path(args.vectors_dir),
        status_path=Path(args.status_output),
        refresh_log_path=Path(args.refresh_log),
        timeout_seconds=args.timeout,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        dimensions=args.dimensions,
        pretty=args.pretty,
        dry_run=args.dry_run,
    )
    indent = 2 if args.pretty else None
    print(json.dumps(summary, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
