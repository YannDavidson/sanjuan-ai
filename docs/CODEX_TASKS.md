# Codex Tasks for SanJuan AI

This file contains the first implementation tasks for Codex or another coding agent.

## Task 1: Initialize monorepo structure

Create the following folders:

```txt
apps/web
apps/api
packages/ingestion
packages/retrieval
packages/shared
data/sources
scripts
docs
```

Add `.gitkeep` files where needed.

## Task 2: Add source registry loader

Build a small Python loader in:

```txt
packages/ingestion/load_sources.py
```

Requirements:

- Read `data/sources/pr_sources.yml`
- Validate required fields:
  - id
  - name
  - url
  - category
  - geography
  - language
  - trust_level
  - source_type
- Print a clean summary table
- Fail with clear error messages if fields are missing

Suggested libraries:

- `pyyaml`
- `pydantic`

## Task 3: Add source schema

Create:

```txt
packages/shared/source_schema.py
```

Define a `Source` model with:

```py
id: str
name: str
url: str
category: str
geography: str
language: str
trust_level: str
source_type: str
update_frequency: str | None
notes: str | None
```

## Task 4: Create first API skeleton

Create a FastAPI app in:

```txt
apps/api/main.py
```

Endpoints:

- `GET /health`
- `GET /sources`
- `GET /sources/{source_id}`
- `POST /ask`

For now, `/ask` can return a placeholder response:

```json
{
  "answer": "SanJuan AI is not connected to retrieval yet.",
  "sources": []
}
```

## Task 5: Create first web UI skeleton

Create a Next.js app in:

```txt
apps/web
```

MVP pages:

- `/`
- `/ask`
- `/sources`

Visual direction:

- Clean, modern, Caribbean intelligence feel
- Bilingual-ready
- Dark mode support
- Primary message: “Modern Caribbean Intelligence for Puerto Rico”

## Task 6: Build source directory UI

On `/sources`, show:

- Source name
- Category
- Geography
- Trust level
- Language
- URL

Filters:

- category
- trust level
- geography
- language

## Task 7: Add retrieval planning notes

Create:

```txt
docs/RETRIEVAL_PLAN.md
```

Include:

- chunking strategy
- metadata strategy
- citation strategy
- trust weighting
- bilingual retrieval
- safety behavior for high-risk topics

## Task 8: Add first ingestion script

Create:

```txt
packages/ingestion/fetch_static_page.py
```

Requirements:

- Accept a URL
- Fetch HTML
- Extract title
- Extract visible text
- Return JSON with:
  - url
  - title
  - text
  - fetched_at
  - content_hash

Use this only for public pages that allow basic fetching.
