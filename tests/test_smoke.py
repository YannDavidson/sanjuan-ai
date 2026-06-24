"""Local development smoke tests for the SanJuan AI MVP.

These tests intentionally avoid network access and do not require generated corpus
artifacts. They protect imports, source validation, retrieval fallbacks, and the
FastAPI response contract.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.config import DEFAULT_DEV_CORS_ORIGINS, load_api_settings, parse_bool_env, parse_csv_env, parse_int_env
from apps.api.main import app
from apps.api.rate_limit import InMemoryRateLimiter
from packages.ingestion.corpus_status import build_corpus_status
from packages.ingestion.load_sources import load_sources
from packages.ingestion.refresh_corpus import refresh_corpus
from packages.retrieval.hybrid_search import search_hybrid
from packages.retrieval.keyword_search import search_chunks
from packages.shared.answer_schema import AskAnswer


def test_source_registry_loads_registered_sources() -> None:
    sources = load_sources()

    assert len(sources) >= 10
    assert any(source.id == "pr_gov_main" for source in sources)
    assert all(source.id for source in sources)
    assert all(source.url for source in sources)


def test_api_settings_parse_cors_origins(monkeypatch) -> None:
    monkeypatch.setenv("SANJUAN_ENV", "production")
    monkeypatch.setenv("SANJUAN_CORS_ORIGINS", "https://sanjuan-ai.example.com, https://www.sanjuan-ai.example.com")
    settings = load_api_settings()

    assert settings.is_production is True
    assert settings.cors_origins == ("https://sanjuan-ai.example.com", "https://www.sanjuan-ai.example.com")
    assert parse_csv_env("a, b,,c") == ("a", "b", "c")


def test_api_settings_default_dev_cors(monkeypatch) -> None:
    monkeypatch.delenv("SANJUAN_ENV", raising=False)
    monkeypatch.delenv("SANJUAN_CORS_ORIGINS", raising=False)
    settings = load_api_settings()

    assert settings.environment == "development"
    assert settings.cors_origins == DEFAULT_DEV_CORS_ORIGINS


def test_api_settings_parse_rate_limit_env(monkeypatch) -> None:
    monkeypatch.setenv("SANJUAN_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("SANJUAN_ASK_RATE_LIMIT_PER_MINUTE", "5")
    settings = load_api_settings()

    assert settings.rate_limit_enabled is False
    assert settings.ask_rate_limit_per_minute == 5
    assert parse_bool_env("yes") is True
    assert parse_bool_env("off", default=True) is False
    assert parse_int_env("bad", default=7, minimum=1) == 7
    assert parse_int_env("0", default=7, minimum=1) == 1


def test_in_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    first = limiter.check("client-a", now=100.0)
    second = limiter.check("client-a", now=101.0)
    third = limiter.check("client-a", now=102.0)
    later = limiter.check("client-a", now=161.1)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds > 0
    assert later.allowed is True


def test_corpus_status_handles_missing_directories(tmp_path: Path) -> None:
    status = build_corpus_status(
        raw_dir=tmp_path / "missing-raw",
        chunks_dir=tmp_path / "missing-chunks",
        vectors_dir=tmp_path / "missing-vectors",
    )

    assert status.ready_for_keyword_retrieval is False
    assert status.ready_for_vector_retrieval is False
    assert status.raw_documents_count == 0
    assert status.chunks_count == 0
    assert status.vectors_count == 0
    assert status.warnings


def test_keyword_search_returns_safe_empty_results_for_missing_chunks(tmp_path: Path) -> None:
    results = search_chunks(query="business registration Puerto Rico", chunks_dir=tmp_path / "chunks")

    assert results == []


def test_hybrid_search_returns_safe_empty_results_for_missing_artifacts(tmp_path: Path) -> None:
    results = search_hybrid(
        query="business registration Puerto Rico",
        chunks_dir=tmp_path / "chunks",
        vectors_dir=tmp_path / "vectors",
    )

    assert results == []


def test_refresh_corpus_dry_run_avoids_network_and_writes(tmp_path: Path) -> None:
    summary = refresh_corpus(
        raw_dir=tmp_path / "raw",
        chunks_dir=tmp_path / "chunks",
        vectors_dir=tmp_path / "vectors",
        status_path=tmp_path / "status" / "source_status.json",
        refresh_log_path=tmp_path / "status" / "last_refresh.json",
        dry_run=True,
    )

    assert summary["mode"] == "dry_run"
    assert summary["network_required"] is False
    assert summary["writes_artifacts"] is False
    assert summary["would_require_network"] is True
    assert summary["would_write_artifacts"] is True
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "status" / "last_refresh.json").exists()


def test_fastapi_health_endpoint_includes_corpus_status_and_security_headers() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "sanjuan-ai-api"
    assert "environment" in payload
    assert "cors_configured" in payload
    assert "rate_limit_enabled" in payload
    assert "ask_rate_limit_per_minute" in payload
    assert "corpus" in payload
    assert "ready_for_keyword_retrieval" in payload["corpus"]


def test_fastapi_sources_endpoint_returns_registry() -> None:
    client = TestClient(app)
    response = client.get("/sources")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 10
    assert any(source["id"] == "pr_gov_main" for source in payload["sources"])


def test_fastapi_ask_endpoint_matches_answer_contract_and_rate_limit_headers() -> None:
    client = TestClient(app)
    response = client.post("/ask", json={"question": "business registration Puerto Rico", "language": "en"})

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    answer = AskAnswer(**response.json())
    assert answer.answer
    assert answer.language == "en"
    assert answer.confidence in {"high", "medium", "low", "placeholder"}
    assert answer.ingestion_status is not None
