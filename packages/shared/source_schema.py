"""Source registry schemas for SanJuan AI.

The source registry is the foundation for SanJuan AI's trusted retrieval layer.
Every source record should be explicit about provenance, geography, language,
and trust level so future ingestion and answer-generation systems can reason
about what to cite.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


TrustLevel = Literal["official", "institutional", "community", "experimental"]
LanguageCode = Literal["en", "es", "en-es", "multi"]


class CrawlRules(BaseModel):
    """Bounded crawl settings for one source.

    Crawling is opt-in per source. The defaults are intentionally conservative:
    no crawling unless enabled, a small page cap, no allow-list by default, and
    common noisy or unsafe paths blocked.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    enabled: bool = Field(default=False, description="Whether bounded crawling is enabled for this source.")
    max_pages_per_source: int = Field(default=1, ge=1, le=100)
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)

    @field_validator("allowed_paths", "blocked_paths")
    @classmethod
    def normalize_paths(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            path = value.strip()
            if not path:
                continue
            if not path.startswith("/"):
                path = f"/{path}"
            normalized.append(path.rstrip("/") or "/")
        return sorted(set(normalized))


class Source(BaseModel):
    """A single public information source for Puerto Rico."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=2, description="Stable source identifier.")
    name: str = Field(..., min_length=2, description="Human-readable source name.")
    url: HttpUrl = Field(..., description="Canonical public URL for the source.")
    category: str = Field(..., min_length=2, description="Primary topic category.")
    geography: str = Field(..., min_length=2, description="Geographic coverage.")
    language: LanguageCode = Field(..., description="Primary language for the source.")
    trust_level: TrustLevel = Field(..., description="Source trust classification.")
    source_type: str = Field(..., min_length=2, description="Website, API, PDF, feed, dataset, etc.")
    update_frequency: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    crawl: CrawlRules | None = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("id may only contain letters, numbers, underscores, and hyphens")
        return value

    @field_validator("category", "geography", "source_type")
    @classmethod
    def normalize_slug_like_fields(cls, value: str) -> str:
        return value.lower().replace(" ", "_")


class SourceRegistry(BaseModel):
    """Container for all registered sources."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sources: list[Source] = Field(default_factory=list)

    @field_validator("sources")
    @classmethod
    def validate_unique_source_ids(cls, sources: list[Source]) -> list[Source]:
        seen: set[str] = set()
        duplicates: set[str] = set()

        for source in sources:
            if source.id in seen:
                duplicates.add(source.id)
            seen.add(source.id)

        if duplicates:
            duplicate_list = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate source id(s): {duplicate_list}")

        return sources

    def by_id(self, source_id: str) -> Source | None:
        """Return a source by id, or None when no match exists."""
        return next((source for source in self.sources if source.id == source_id), None)

    def categories(self) -> list[str]:
        """Return sorted source categories."""
        return sorted({source.category for source in self.sources})

    def trust_levels(self) -> list[str]:
        """Return sorted trust levels currently represented in the registry."""
        return sorted({source.trust_level for source in self.sources})
