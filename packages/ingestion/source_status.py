"""Source freshness and health reporting for SanJuan AI.

Run after source ingestion:

    python -m packages.ingestion.source_status --pretty

Generate the JSON artifact used by the web dashboard:

    python -m packages.ingestion.source_status --pretty --write-json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.ingestion.batch_ingest_sources import DEFAULT_OUTPUT_DIR as DEFAULT_RAW_DIR
from packages.ingestion.load_sources import DEFAULT_SOURCE_REGISTRY_PATH, load_sources_from_path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATUS_PATH = REPO_ROOT / "data" / "status" / "source_status.json"
MIN_HEALTHY_TEXT_LENGTH = 500
STALE_AFTER_DAYS = 30


def parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO timestamp into a timezone-aware datetime."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def days_since(value: str | None, now: datetime | None = None) -> int | None:
    """Return whole days since an ISO timestamp."""
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    now = now or datetime.now(timezone.utc)
    return max((now - parsed).days, 0)


def load_raw_document(raw_dir: Path, source_id: str) -> dict[str, Any] | None:
    """Load a raw document for a source if it exists."""
    path = raw_dir / f"{source_id}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file:
        document = json.load(file)
    document["_raw_path"] = str(path)
    return document


def classify_source_status(document: dict[str, Any] | None, now: datetime | None = None) -> tuple[str, str]:
    """Return a user-facing status and reason for a source document."""
    if document is None:
        return "missing", "No raw document has been ingested yet."

    if document.get("status") == "failed":
        return "failed", str(document.get("error") or "Fetch failed.")

    text = str(document.get("text") or "")
    text_length = len(text.strip())
    if text_length == 0:
        return "empty", "Document was fetched but no usable text was extracted."
    if text_length < MIN_HEALTHY_TEXT_LENGTH:
        return "thin", f"Only {text_length} characters of extracted text."

    age_days = days_since(document.get("fetched_at"), now=now)
    if age_days is None:
        return "unknown_freshness", "Document has text, but no valid fetched_at timestamp."
    if age_days > STALE_AFTER_DAYS:
        return "stale", f"Fetched {age_days} days ago."

    return "healthy", f"Fetched {age_days} days ago with {text_length} extracted characters."


def compute_priority(source: Any, status: str) -> str:
    """Classify source review priority."""
    high_value_categories = {
        "government_portal",
        "alerts",
        "health",
        "transportation",
        "taxes",
        "business_registration",
        "economic_development",
        "weather",
        "earthquakes",
    }
    if status in {"failed", "missing", "empty"} and source.trust_level == "official":
        return "high"
    if source.category in high_value_categories and status in {"thin", "stale", "unknown_freshness"}:
        return "medium"
    if source.trust_level == "official" or source.category in high_value_categories:
        return "high_value"
    return "normal"


def build_source_status_report(
    registry_path: Path = DEFAULT_SOURCE_REGISTRY_PATH,
    raw_dir: Path = DEFAULT_RAW_DIR,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build source health and freshness report from registry + raw docs."""
    now = now or datetime.now(timezone.utc)
    sources = load_sources_from_path(registry_path)
    rows: list[dict[str, Any]] = []

    for source in sources:
        document = load_raw_document(raw_dir, source.id)
        status, reason = classify_source_status(document, now=now)
        text = str((document or {}).get("text") or "")
        fetched_at = (document or {}).get("fetched_at")
        row = {
            "source_id": source.id,
            "name": source.name,
            "url": str(source.url),
            "category": source.category,
            "geography": source.geography,
            "language": source.language,
            "trust_level": source.trust_level,
            "source_type": source.source_type,
            "status": status,
            "reason": reason,
            "priority": compute_priority(source, status),
            "status_code": (document or {}).get("status_code"),
            "content_length": (document or {}).get("content_length"),
            "text_length": len(text.strip()),
            "fetched_at": fetched_at,
            "age_days": days_since(fetched_at, now=now),
            "content_hash": (document or {}).get("content_hash"),
            "raw_path": str(Path(document["_raw_path"]).relative_to(REPO_ROOT)) if document and document.get("_raw_path") else None,
            "error": (document or {}).get("error"),
        }
        rows.append(row)

    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        by_priority[row["priority"]] = by_priority.get(row["priority"], 0) + 1

    return {
        "generated_at": now.isoformat(),
        "registry_path": str(registry_path.relative_to(REPO_ROOT)) if registry_path.is_relative_to(REPO_ROOT) else str(registry_path),
        "raw_dir": str(raw_dir.relative_to(REPO_ROOT)) if raw_dir.is_relative_to(REPO_ROOT) else str(raw_dir),
        "total_sources": len(rows),
        "by_status": by_status,
        "by_priority": by_priority,
        "sources": rows,
    }


def write_status_report(report: dict[str, Any], output_path: Path = DEFAULT_STATUS_PATH, pretty: bool = False) -> Path:
    """Write source status report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=indent)
        file.write("\n")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report SanJuan AI source freshness and health.")
    parser.add_argument("--registry", default=str(DEFAULT_SOURCE_REGISTRY_PATH), help="Path to source registry YAML.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="Directory containing raw ingested JSON documents.")
    parser.add_argument("--output", default=str(DEFAULT_STATUS_PATH), help="Output path for JSON status artifact.")
    parser.add_argument("--write-json", action="store_true", help="Write the source status artifact to disk.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_source_status_report(registry_path=Path(args.registry), raw_dir=Path(args.raw_dir))

    if args.write_json:
        write_status_report(report, output_path=Path(args.output), pretty=args.pretty)

    indent = 2 if args.pretty else None
    print(json.dumps(report, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
