# SanJuan AI Development Guide

This guide covers the local commands used by the MVP test and CI workflow.

## Python setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Smoke tests and fixture retrieval tests

Run all tests from the repository root:

```bash
pytest -q
```

The tests intentionally avoid external network access. They check:

- source registry loading
- source crawl-rule validation
- safe crawler URL allow/block behavior
- API runtime settings and CORS parsing
- API rate limit settings parsing
- in-memory rate limiter behavior
- corpus readiness behavior when document directories are missing
- keyword retrieval safe empty fallback
- hybrid retrieval safe empty fallback
- refresh pipeline dry-run behavior
- FastAPI `/health`
- FastAPI `/sources`
- FastAPI `/ask` response contract
- keyword retrieval against committed demo corpus fixtures
- local vector-store generation from fixture chunks
- hybrid retrieval over fixture chunks + generated fixture vectors

## Test fixtures

Retrieval fixtures live under:

```txt
tests/fixtures/corpus/
├── raw/
└── chunks/
```

These fixtures are intentionally small, deterministic, and safe to commit. They are not official Puerto Rico guidance; they are test data for CI.

## Backend

Run the API locally:

```bash
uvicorn apps.api.main:app --reload
```

Open:

```txt
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

Local development CORS defaults allow:

```txt
http://localhost:3000
http://127.0.0.1:3000
```

For production, set `SANJUAN_ENV=production` and `SANJUAN_CORS_ORIGINS=https://your-web-domain.com`.

### API rate limiting

The `/ask` endpoint has a small in-memory MVP rate limiter enabled by default:

```bash
SANJUAN_RATE_LIMIT_ENABLED=true
SANJUAN_ASK_RATE_LIMIT_PER_MINUTE=30
```

Successful `/ask` responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining`. If the limit is exceeded, `/ask` returns HTTP `429` with `Retry-After`.

This limiter is useful for local demos and a single-process deployment. It is not enough by itself for scaled production. Read `docs/API_ABUSE_PROTECTION.md` before public exposure.

## Web app

Run the web app:

```bash
cd apps/web
npm install
npm run dev
```

Open:

```txt
http://localhost:3000
```

## Full local retrieval flow

When you want real local retrieval artifacts, run the single refresh command:

```bash
python -m packages.ingestion.refresh_corpus --pretty
```

Equivalent manual steps:

```bash
python -m packages.ingestion.batch_ingest_sources --pretty
python -m packages.ingestion.source_status --pretty --write-json
python -m packages.retrieval.chunk_documents --pretty
python -m packages.retrieval.local_vector_search build --pretty
python -m packages.retrieval.hybrid_search "business registration Puerto Rico" --pretty
```

To inspect the scheduler plan without network access or writes:

```bash
python -m packages.ingestion.refresh_corpus --dry-run --pretty
```

Then start the API and web app.

## Bounded source crawling

Homepage-only ingestion remains the default:

```bash
python -m packages.ingestion.batch_ingest_sources --pretty
```

To crawl selected internal pages for sources with `crawl.enabled=true`:

```bash
python -m packages.ingestion.batch_ingest_sources --crawl --pretty
```

For safer local testing, override the page cap:

```bash
python -m packages.ingestion.batch_ingest_sources --crawl --max-pages 3 --pretty
```

To debug one source:

```bash
python -m packages.ingestion.safe_crawler pr_gov_main --max-pages 3 --pretty
```

Read `docs/CRAWLING_RULES.md` before increasing crawl depth.

## Deployment checks

Before deployment, run:

```bash
pytest -q
cd apps/web
npm install
npm run build
```

Read `docs/DEPLOYMENT.md` for backend and web deployment configuration. Read `docs/SCHEDULER_PLAN.md` for scheduled ingestion options.

## CI

GitHub Actions runs on pushes and pull requests to `main`.

The main CI workflow checks:

1. Python dependency install
2. `pytest -q`
3. Web dependency install
4. `npm run build` for `apps/web`

A second scheduled workflow runs daily and can be triggered manually:

```txt
.github/workflows/refresh-dry-run.yml
```

It checks:

1. Python dependency install
2. `pytest -q`
3. `python -m packages.ingestion.refresh_corpus --dry-run --pretty`

The CI workflows do not require secrets or live website fetching for retrieval tests.
