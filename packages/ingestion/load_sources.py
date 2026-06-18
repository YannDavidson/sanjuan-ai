"""Load and validate the SanJuan AI Puerto Rico source registry.

Usage from the repository root:

    python -m packages.ingestion.load_sources
    python -m packages.ingestion.load_sources --json
    python -m packages.ingestion.load_sources --path data/sources/pr_sources.yml
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from packages.shared.source_schema import Source, SourceRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_REGISTRY_PATH = REPO_ROOT / "data" / "sources" / "pr_sources.yml"


class SourceRegistryError(RuntimeError):
    """Raised when the source registry cannot be loaded or validated."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SourceRegistryError(f"Source registry not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise SourceRegistryError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        raise SourceRegistryError(f"Source registry is empty: {path}")

    if not isinstance(data, dict):
        raise SourceRegistryError("Source registry root must be a mapping with a 'sources' key.")

    return data


def load_registry(path: Path | str = DEFAULT_SOURCE_REGISTRY_PATH) -> SourceRegistry:
    """Load and validate a source registry file."""
    registry_path = Path(path)
    raw_data = _read_yaml(registry_path)

    try:
        return SourceRegistry.model_validate(raw_data)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            location = " -> ".join(str(part) for part in error.get("loc", []))
            message = error.get("msg", "validation error")
            errors.append(f"- {location}: {message}")

        detail = "\n".join(errors)
        raise SourceRegistryError(f"Source registry validation failed:\n{detail}") from exc


def load_sources_from_path(path: Path | str) -> list[Source]:
    """Load sources from a specific source registry file path."""
    return load_registry(path).sources


def load_sources() -> list[Source]:
    """Load sources from the default Puerto Rico source registry."""
    return load_registry(DEFAULT_SOURCE_REGISTRY_PATH).sources


def summarize_sources(sources: list[Source]) -> str:
    """Return a readable summary grouped by category and trust level."""
    category_counts = Counter(source.category for source in sources)
    trust_counts = Counter(source.trust_level for source in sources)
    language_counts = Counter(source.language for source in sources)

    lines = [
        "SanJuan AI source registry summary",
        "===================================",
        f"Total sources: {len(sources)}",
        "",
        "By category:",
    ]

    for category, count in sorted(category_counts.items()):
        lines.append(f"  - {category}: {count}")

    lines.extend(["", "By trust level:"])
    for trust_level, count in sorted(trust_counts.items()):
        lines.append(f"  - {trust_level}: {count}")

    lines.extend(["", "By language:"])
    for language, count in sorted(language_counts.items()):
        lines.append(f"  - {language}: {count}")

    lines.extend(["", "Sources:"])
    for source in sorted(sources, key=lambda item: item.id):
        lines.append(
            f"  - {source.id} | {source.name} | {source.category} | "
            f"{source.trust_level} | {source.language} | {source.url}"
        )

    return "\n".join(lines)


def sources_to_json(sources: list[Source]) -> str:
    """Serialize sources as pretty JSON."""
    payload = [source.model_dump(mode="json") for source in sources]
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and summarize the SanJuan AI source registry.")
    parser.add_argument(
        "--path",
        default=str(DEFAULT_SOURCE_REGISTRY_PATH),
        help="Path to a source registry YAML file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print validated sources as JSON instead of the text summary.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        sources = load_sources_from_path(args.path)
    except SourceRegistryError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")

    if args.json:
        print(sources_to_json(sources))
    else:
        print(summarize_sources(sources))


if __name__ == "__main__":
    main()
