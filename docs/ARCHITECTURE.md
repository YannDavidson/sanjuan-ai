# SanJuan AI Architecture

SanJuan AI is a Puerto Rico-first public intelligence layer. It combines official sources, local context, search, retrieval, and bilingual AI.

## Product direction

SanJuan AI should become more than a chatbot. It should support:

- A public web assistant
- An embeddable widget
- Puerto Rico source registry
- Government and service knowledge base
- Tourism and local discovery layer
- Business and startup support layer
- Emergency and weather awareness layer
- Future municipal dashboards

## Core architecture

```txt
Public Sources
  ↓
Ingestion Layer
  ↓
Knowledge Store: Postgres + pgvector
  ↓
Retrieval Layer: keyword + semantic search
  ↓
AI Answer Layer: bilingual, cited, source-grounded
  ↓
Frontend / Widget / API Consumers
```

## Main components

### 1. Source registry

Every source should include:

- id
- name
- url
- category
- geography
- language
- trust_level
- source_type
- update_frequency
- notes

Trust levels:

- `official`: government, agency, public authority, federal source
- `institutional`: universities, recognized nonprofits, chambers, public-private organizations
- `community`: local directories, community groups, media, cultural calendars
- `experimental`: unverified or new source

### 2. Ingestion layer

The ingestion layer should support:

- Static web pages
- RSS feeds
- APIs
- PDFs
- CSV/JSON datasets
- Manual source entries

For each document, store:

- source ID
- original URL
- title
- raw text
- cleaned text
- language
- timestamp fetched
- timestamp updated, if available
- content hash
- category
- geographic relevance
- chunk records for search

### 3. Retrieval layer

Retrieval should combine:

- Keyword search
- Vector search
- Source trust weighting
- Recency weighting
- Geographic filtering
- Category filtering
- Language preference

Every answer should return citations where possible.

### 4. AI answer layer

The assistant should follow these rules:

- Never invent official requirements.
- For permits, taxes, health, safety, emergencies, and legal questions, answer only from trusted sources.
- Clearly say when the system does not know.
- Cite the source page.
- Offer next-step links.
- Support English and Spanish.
- Avoid sounding bureaucratic; keep the assistant friendly and useful.

## MVP technical stack

Recommended:

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `packages/ingestion`: source loaders
- `packages/retrieval`: search and RAG
- `packages/shared`: schemas, config, types
- Database: Postgres + pgvector
- Deployment: Vercel + Supabase/Neon + Render/Fly.io

## Initial data model

### sources

```sql
CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  category TEXT NOT NULL,
  geography TEXT,
  language TEXT,
  trust_level TEXT NOT NULL,
  source_type TEXT,
  update_frequency TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### documents

```sql
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  source_id TEXT REFERENCES sources(id),
  url TEXT NOT NULL,
  title TEXT,
  raw_text TEXT,
  cleaned_text TEXT,
  language TEXT,
  content_hash TEXT,
  fetched_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### chunks

```sql
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT REFERENCES documents(id),
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## High-risk topics

For medical, emergency, legal, immigration, taxes, permits, public benefits, court, or police-related questions, SanJuan AI should:

- Use official sources only
- Cite clearly
- Avoid definitive claims when source is outdated
- Recommend contacting the relevant agency when needed
- Include emergency disclaimers for urgent situations

## Future expansion

- All 78 municipalities
- WhatsApp assistant
- Voice assistant
- Open data dashboard
- Startup and grant finder
- Permit navigator
- Tourism concierge
- Local business discovery
- Municipal white-label versions
- API for civic organizations and agencies
