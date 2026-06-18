"""Shared answer and citation schemas for SanJuan AI."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

ConfidenceLevel = Literal["high", "medium", "low", "placeholder"]


class Citation(BaseModel):
    """Specific evidence used to support an answer."""

    source_id: str = Field(..., description="Registry source id.")
    source_name: str = Field(..., description="Human-readable source name.")
    title: str | None = Field(default=None, description="Document or page title.")
    url: HttpUrl = Field(..., description="URL for the cited source or page.")
    trust_level: str = Field(..., description="Source trust level, such as official or institutional.")
    snippet: str | None = Field(default=None, description="Short evidence excerpt or summary.")
    fetched_at: str | None = Field(default=None, description="Timestamp when the evidence was fetched.")


class AnswerSource(BaseModel):
    """Broader source card that may be useful even before full retrieval exists."""

    source_id: str
    source_name: str
    url: HttpUrl
    category: str
    geography: str
    language: str
    trust_level: str


class AskAnswer(BaseModel):
    """Citation-first response contract for /ask."""

    answer: str
    language: str = Field(default="en", description="Response language.")
    confidence: ConfidenceLevel = Field(default="placeholder")
    citations: list[Citation] = Field(default_factory=list)
    sources: list[AnswerSource] = Field(default_factory=list)
    safety_note: str | None = None
