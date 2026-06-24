# Source Ingestion Scheduler Plan

SanJuan AI currently uses local file-based corpus artifacts:

```txt
data/documents/raw/
data/documents/chunks/
data/documents/vectors/
data/status/source_status.json
data/status/last_refresh.json
```

The scheduler goal is to refresh those artifacts on a predictable cadence without making the public `/ask` API responsible for slow live website fetching.

## Refresh command

Run the full refresh pipeline from the repository root:

```bash
python -m packages.ingestion.refresh_corpus --pretty
```

This executes:

1. `batch_ingest_sources`
2. `source_status`
3. `chunk_documents`
4. `local_vector_search build`
5. writes `data/status/last_refresh.json`

For CI/docs checks that should not fetch live websites:

```bash
python -m packages.ingestion.refresh_corpus --dry-run --pretty
```

## GitHub Actions dry-run check

The repository includes a dedicated scheduled workflow:

```txt
.github/workflows/refresh-dry-run.yml
```

It runs:

```bash
pytest -q
python -m packages.ingestion.refresh_corpus --dry-run --pretty
```

The workflow supports:

- `workflow_dispatch` for manual checks
- a daily cron schedule at `09:15 UTC`

This intentionally does **not** fetch live websites or write corpus artifacts. Its purpose is to keep the scheduler wrapper, imports, and dry-run path healthy in CI.

## Recommended cadence

For the MVP:

- **Official alerts/weather/emergency sources:** every 1–3 hours later, once category-specific refresh exists.
- **General government/service pages:** daily.
- **Tourism and institutional pages:** daily or weekly.
- **Static reference pages:** weekly.

Until the project has category-specific scheduling, run the full pipeline daily or manually before demos.

## Local cron example

```cron
0 5 * * * cd /path/to/sanjuan-ai && /path/to/python -m packages.ingestion.refresh_corpus >> data/status/refresh.log 2>&1
```

## Hosted scheduler options

### Render cron job

Create a separate Render Cron Job using:

```bash
python -m packages.ingestion.refresh_corpus
```

Important: local filesystem artifacts may not persist across services unless the host provides persistent disk or object storage. For a serious production deployment, move raw documents, chunks, vectors, and source status into Postgres/object storage.

### GitHub Actions scheduled workflow

A scheduled GitHub Actions workflow can run the refresh pipeline, but committing generated artifacts back to the repo should be handled carefully. For now, CI should not hit live websites. Use `--dry-run` in CI.

### Future production architecture

Longer-term scheduler architecture:

```txt
scheduler/cron
  -> source registry
  -> fetch queue
  -> raw document storage
  -> chunking job
  -> embedding/vector job
  -> source status artifact/dashboard
  -> API reads from persistent store
```

## Failure behavior

The refresh pipeline should continue when one source fails. Failed sources are recorded in raw JSON documents and surfaced in the status dashboard.

Expected failure types:

- network timeout
- non-200 response
- page blocks generic fetchers
- no useful text extracted
- source changed structure

The dashboard should be used to decide whether a source needs a custom loader, replacement, or lower priority.

## Current MVP limitation

The pipeline fetches source homepages only. It does not yet crawl internal links, parse PDFs, or use APIs deeply. That is intentional for the first stable foundation.
