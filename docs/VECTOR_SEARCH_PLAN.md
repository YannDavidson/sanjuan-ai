# Vector Search Plan

## Purpose

SanJuan AI currently uses local keyword retrieval over JSON chunks. That is the correct MVP baseline because it is transparent, cheap, and easy to debug. The next retrieval layer is semantic search: matching the meaning of a question to Puerto Rico source chunks even when the exact words do not match.

This document defines the vector-search path without requiring paid API keys or external services yet.

## MVP principle

Keyword retrieval remains the default production-safe path until embeddings are generated and evaluated.

The vector layer should be additive:

1. Keep keyword search working.
2. Add local embedding/vector scaffolding.
3. Store vector metadata beside chunk metadata.
4. Later replace local hashing vectors with model embeddings.
5. Eventually move storage to Postgres + pgvector.

## Retrieval modes

SanJuan AI should support three modes:

| Mode | Description | Status |
| --- | --- | --- |
| `keyword` | Exact/token keyword retrieval over local chunks | Implemented |
| `local_vector` | Local hashed vector retrieval, no external API needed | MVP scaffold |
| `hybrid` | Keyword + vector reranking | Planned |

## Local vector scaffold

The first vector implementation uses deterministic hashed bag-of-words vectors. This is not as strong as real language-model embeddings, but it gives the repo a working semantic-search interface without API keys.

Benefits:

- Safe to run locally
- Deterministic
- Free
- Works in CI/dev environments
- Creates the same result shape future embeddings should return
- Lets the backend and web app be designed before provider selection

Limitations:

- Not true semantic understanding
- Cannot capture deep synonyms or multilingual meaning well
- Should not be marketed as production-grade vector search

## Future embedding providers

Later options:

- OpenAI embeddings
- Cohere embeddings
- Voyage AI embeddings
- SentenceTransformers local models
- Multilingual embeddings for English/Spanish Puerto Rico content

Provider selection should prioritize:

- Spanish/English quality
- Low latency
- Cost control
- Strong retrieval performance on Puerto Rico civic topics
- Data handling and privacy guarantees

## Embedding record schema

Each vector record should preserve citation-critical metadata:

```json
{
  "embedding_id": "chunk_id:embedding:provider:model",
  "chunk_id": "...",
  "document_id": "...",
  "source_id": "...",
  "source_name": "...",
  "source_url": "...",
  "title": "...",
  "category": "...",
  "geography": "...",
  "language": "...",
  "trust_level": "official",
  "provider": "local_hash",
  "model": "hashing-vector-v1",
  "dimensions": 384,
  "vector": [0.0, 0.12, 0.0],
  "created_at": "2026-06-20T00:00:00Z",
  "content_hash": "...",
  "citation": {
    "title": "...",
    "url": "...",
    "source_id": "...",
    "source_name": "..."
  }
}
```

## Storage path for MVP

Local vector records should live in:

```txt
data/documents/vectors/
```

One file per document:

```txt
data/documents/vectors/{document_id}.vectors.json
```

## Future pgvector table

```sql
CREATE TABLE chunk_embeddings (
  embedding_id TEXT PRIMARY KEY,
  chunk_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
  embedding VECTOR,
  metadata JSONB,
  content_hash TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Hybrid ranking plan

Hybrid search should combine:

- Keyword score
- Vector cosine similarity
- Trust level boost
- Geography boost
- Recency/freshness boost
- Language match boost
- High-risk official-source gating

Suggested MVP formula:

```txt
final_score =
  0.45 * normalized_keyword_score +
  0.35 * normalized_vector_score +
  0.10 * trust_boost +
  0.05 * geography_boost +
  0.05 * language_boost
```

## High-risk topic behavior

For permits, taxes, health, legal, immigration, emergency, benefits, police, and court topics:

- Prefer official sources.
- Do not answer from community or experimental sources alone.
- If official evidence is missing, return a safe fallback.
- Always cite source pages.

## Evaluation set

Create test questions such as:

- How do I register a business in Puerto Rico?
- Where can I find San Juan municipal services?
- What agency handles Puerto Rico tax registration?
- What is the weather authority for San Juan alerts?
- Where can I find tourism information for Puerto Rico?
- ¿Cómo registro un negocio en Puerto Rico?
- ¿Dónde encuentro servicios municipales de San Juan?

Track:

- Top 3 source quality
- Citation accuracy
- Language correctness
- Official-source behavior for high-risk questions
- Empty-result fallback quality

## Implementation sequence

1. Add local vector schema.
2. Generate local hash vectors from chunks.
3. Add local vector search CLI.
4. Compare keyword and local vector results.
5. Add hybrid retrieval.
6. Add real embeddings provider later.
7. Migrate vectors to pgvector when ready.
