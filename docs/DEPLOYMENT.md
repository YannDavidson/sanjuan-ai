# SanJuan AI Deployment

This document describes the first deployment-ready setup for the SanJuan AI MVP.

The project currently has two deployable services:

1. **API service** — FastAPI backend in `apps/api`
2. **Web service** — Next.js frontend in `apps/web`

The backend and frontend can be deployed separately. The web app talks to the API through the `NEXT_PUBLIC_SANJUAN_API_URL` environment variable.

## Backend deployment

### Production start command

From the repository root:

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Required files

- `requirements.txt`
- `apps/api/main.py`
- `render.yaml` for Render-style deployment
- `Dockerfile.api` for container deployment

### Render-style setup

The included `render.yaml` defines a web service named `sanjuan-ai-api`.

Default values:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

### Backend environment variables

Recommended production variables:

```bash
SANJUAN_ENV=production
SANJUAN_API_VERSION=0.6.0
SANJUAN_CORS_ORIGINS=https://your-web-domain.com
SANJUAN_CORS_ALLOW_CREDENTIALS=false
SANJUAN_RETRIEVAL_MODE=hybrid
SANJUAN_RATE_LIMIT_ENABLED=true
SANJUAN_ASK_RATE_LIMIT_PER_MINUTE=30
```

Keep only one `SANJUAN_API_VERSION` value in production. The current MVP version is `0.6.0`.

`SANJUAN_CORS_ORIGINS` is a comma-separated list. In production, set it explicitly to the deployed web origin. In local development, the API defaults to:

```bash
http://localhost:3000,http://127.0.0.1:3000
```

The API also adds conservative security headers, including `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.

`/ask` includes MVP in-memory rate limiting. This is useful for single-process demos, but public production traffic should also use an edge proxy, API gateway, or Redis-backed limiter. Read `docs/API_ABUSE_PROTECTION.md` before public exposure.

## Web deployment

### Production build

From `apps/web`:

```bash
npm install
npm run build
npm run start
```

### Required environment variable

```bash
NEXT_PUBLIC_SANJUAN_API_URL=https://your-api-domain.com
```

For local development, this defaults to:

```bash
http://127.0.0.1:8000
```

### Vercel-style setup

The included `apps/web/vercel.json` configures the Next.js app as the web project root.

On Vercel, use:

- Framework preset: Next.js
- Root directory: `apps/web`
- Build command: `npm run build`
- Output: Next.js default

Set:

```bash
NEXT_PUBLIC_SANJUAN_API_URL=https://your-api-domain.com
```

## Source refresh / scheduler

The refresh pipeline is exposed through one command:

```bash
python -m packages.ingestion.refresh_corpus --pretty
```

This runs:

1. batch source ingestion
2. source status generation
3. document chunking
4. local vector build
5. refresh summary artifact generation

For scheduler planning without live fetching or writes:

```bash
python -m packages.ingestion.refresh_corpus --dry-run --pretty
```

The repository also includes `.github/workflows/refresh-dry-run.yml`, a scheduled/manual GitHub Actions workflow that validates the dry-run path daily without live fetching.

Read `docs/SCHEDULER_PLAN.md` for hosted cron options and recommended cadence.

## Container deployment

Build the API container from the repository root:

```bash
docker build -f Dockerfile.api -t sanjuan-ai-api .
docker run -p 8000:8000 sanjuan-ai-api
```

Then open:

```txt
http://127.0.0.1:8000/health
```

## Deployment checklist

Before deploying:

```bash
pip install -r requirements.txt
pytest -q
cd apps/web
npm install
npm run build
```

After deploying:

1. Open `/health` on the API.
2. Confirm the response includes `status: ok`.
3. Confirm `cors_configured: true` in production.
4. Confirm `rate_limit_enabled: true` unless intentionally disabled.
5. Set `NEXT_PUBLIC_SANJUAN_API_URL` in the web app.
6. Open `/ask` and submit a test question.
7. Confirm `/ask` responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining`.
8. Open `/sources` and `/status`.

## Current MVP limitation

The production API currently reads local file-based corpus artifacts from the repository filesystem. For a real hosted deployment, run ingestion/chunking/vector generation before deployment or mount/persist generated artifacts.

Recommended future upgrade:

- Move documents/chunks/vectors into Postgres + pgvector or object storage.
- Run source refresh through a scheduled worker/cron service.
- Add an admin-only source refresh endpoint or queue-backed job trigger.
- Move API rate limiting to edge/API-gateway/Redis-backed infrastructure.
