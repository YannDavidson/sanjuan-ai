# SanJuan AI API

FastAPI backend for SanJuan AI's Puerto Rico source registry, local ingestion pipeline, hybrid retrieval layer, and citation-first `/ask` endpoint.

## Run locally

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Then open:

- API docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>
- Sources: <http://127.0.0.1:8000/sources>

## Smoke tests

Run lightweight local checks before pushing changes:

```bash
pytest -q
```

The smoke tests do not require network access or generated corpus artifacts. They check source loading, corpus readiness, safe retrieval fallbacks, and the FastAPI `/health`, `/sources`, and `/ask` contracts.

## Endpoints

### `GET /health`

Returns service health and local corpus readiness.

```json
{
  "status": "ok",
  "service": "sanjuan-ai-api",
  "corpus": {
    "ready_for_keyword_retrieval": true,
    "ready_for_vector_retrieval": false,
    "raw_documents_count": 15,
    "chunks_count": 80,
    "vectors_count": 0,
    "warnings": [
      "No vector artifacts found. Hybrid retrieval will use keyword-only fallback until vectors are built."
    ]
  }
}
```

### `GET /sources`

Returns the validated Puerto Rico source registry.

Optional query filters:

- `category`
- `trust_level`
- `geography`
- `language`

Example:

```bash
curl "http://127.0.0.1:8000/sources?trust_level=official&language=es"
```

### `GET /sources/{source_id}`

Returns a single source by ID.

Example:

```bash
curl "http://127.0.0.1:8000/sources/pr_gov_main"
```

### `POST /ask`

Citation-first assistant endpoint. The MVP now uses local **hybrid retrieval**, combining keyword search with local vector search when vector artifacts exist. It returns extractive answers from the top evidence block and does not call an external LLM yet.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I register a business in Puerto Rico?","language":"en"}'
```

The response includes:

- `answer`
- `language`
- `confidence`
- `citations`
- `sources`
- `safety_note`
- `ingestion_status`

If no chunks are available or no evidence is found, `/ask` returns a clear fallback instead of guessing. The `ingestion_status` object explains whether raw documents, chunks, or vectors are missing.

## Validate source registry

From the repository root:

```bash
python -m packages.ingestion.load_sources
python -m packages.ingestion.load_sources --json
```

## Fetch a static page

Use the first static page ingestion script to fetch and normalize public HTML content:

```bash
python -m packages.ingestion.fetch_static_page https://www.pr.gov/ --pretty
```

The command returns JSON with:

- `url`
- `title`
- `text`
- `fetched_at`
- `content_hash`
- `status_code`
- `content_length`

## Batch ingest registered sources

Create one raw JSON document per registered source:

```bash
python -m packages.ingestion.batch_ingest_sources --pretty
```

By default, output is written to:

```txt
data/documents/raw/
```

Each document includes source metadata, fetch status, page title, normalized text, fetch timestamp, content hash, status code, content length, and structured error details when a source cannot be fetched.

Useful options:

```bash
python -m packages.ingestion.batch_ingest_sources \
  --registry data/sources/pr_sources.yml \
  --output-dir data/documents/raw \
  --timeout 20 \
  --pretty
```

## Chunk documents for retrieval

After batch ingestion, split raw documents into citation-ready chunks:

```bash
python -m packages.retrieval.chunk_documents --pretty
```

By default, chunks are read from and written to:

```txt
Input:  data/documents/raw/
Output: data/documents/chunks/
```

Each chunk preserves citation-critical metadata:

- stable `chunk_id`
- `document_id`
- `chunk_index`
- chunk text
- character count
- source ID and name
- source URL
- page title
- trust level
- category
- geography
- language
- fetched timestamp
- content hash
- citation object

Useful options:

```bash
python -m packages.retrieval.chunk_documents \
  --input-dir data/documents/raw \
  --output-dir data/documents/chunks \
  --chunk-size 1200 \
  --chunk-overlap 200 \
  --pretty
```

## Search local chunks

Run local keyword retrieval over chunked documents:

```bash
python -m packages.retrieval.keyword_search "business registration Puerto Rico" --pretty
```

Useful filters:

```bash
python -m packages.retrieval.keyword_search "permit" \
  --trust-level official \
  --language es \
  --limit 5 \
  --pretty
```

The keyword layer ranks chunks using exact phrase matches, token overlap, metadata matches, and source trust boosts. It is intentionally simple and transparent for the MVP.

## Build and search local vectors

Build the local deterministic vector store:

```bash
python -m packages.retrieval.local_vector_search build --pretty
```

Search local vectors:

```bash
python -m packages.retrieval.local_vector_search search "business registration Puerto Rico" --pretty
```

## Hybrid retrieval

Hybrid retrieval combines keyword and vector results, deduplicates by `chunk_id`, preserves citation metadata, and falls back to keyword-only behavior when vectors are missing.

```bash
python -m packages.retrieval.hybrid_search "business registration Puerto Rico" --pretty
```

## End-to-end local data flow

```bash
python -m packages.ingestion.batch_ingest_sources --pretty
python -m packages.retrieval.chunk_documents --pretty
python -m packages.retrieval.local_vector_search build --pretty
python -m packages.retrieval.hybrid_search "business registration Puerto Rico" --pretty
uvicorn apps.api.main:app --reload
```

Then test `/ask`:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"business registration Puerto Rico","language":"en"}'
```

## Development and CI

See [`docs/DEVELOPMENT.md`](../../docs/DEVELOPMENT.md) for the local development workflow, smoke test details, and GitHub Actions CI behavior.
