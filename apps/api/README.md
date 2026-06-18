# SanJuan AI API

FastAPI backend for SanJuan AI's Puerto Rico source registry and future retrieval layer.

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

## Endpoints

### `GET /health`

Returns service health.

```json
{
  "status": "ok",
  "service": "sanjuan-ai-api"
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

Placeholder assistant endpoint until retrieval is connected. It already returns the citation-first answer contract used by the web UI.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I register a business in Puerto Rico?","language":"en"}'
```

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
