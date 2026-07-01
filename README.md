# SanJuan AI KB (Knowledge Base)

**SanJuan AI KB** is an AI-native civic intelligence platform for Puerto Rico, starting in San Juan and expanding island-wide. The goal is to help residents, founders, visitors, government partners, and local organizations find trustworthy, bilingual, up-to-date information about Puerto Rico through a modern AI assistant and public data layer.

> Modern Caribbean Intelligence — built for Puerto Rico first.

## Why this exists

Puerto Rico has important information spread across many places: government portals, agency websites, permits, public safety alerts, tourism pages, business resources, municipal pages, health information, weather, transportation, and community services.

SanJuan AI KB turns that fragmented information into a searchable, explainable, bilingual knowledge system.

## What we are building first

1. **Puerto Rico source registry** — a curated list of official, semi-official, and high-value public sources.
2. **Ingestion pipeline** — fetch, normalize, timestamp, and store public content.
3. **Search and retrieval layer** — semantic search over Puerto Rico-specific information.
4. **Bilingual AI assistant** — English and Spanish responses with source links.
5. **San Juan-first user experience** — a clean web app and embeddable widget.
6. **Civic + startup use cases** — government services, permits, business resources, tourism, transportation, emergency/weather alerts, and local opportunity discovery.

## MVP scope

### Phase 1: Knowledge foundation

- Build a verified source list for Puerto Rico.
- Create basic loaders for official public pages.
- Store source metadata: title, URL, category, geography, update frequency, language, and trust level.
- Add citation-first retrieval so answers can point back to source pages.

### Phase 2: Assistant prototype

- Add a simple chat API.
- Add retrieval-augmented generation over the Puerto Rico source index.
- Support English and Spanish.
- Include answer safety rules: do not invent government procedures, fees, office hours, eligibility requirements, or emergency instructions.

### Phase 3: San Juan public demo

- Launch a public landing page.
- Add a small widget: “Ask SanJuan AI.”
- Prioritize San Juan metro questions first, then expand to all 78 municipalities.

## Technical stack

- **Frontend:** Next.js / React
- **Backend:** FastAPI or Next.js API routes
- **Database:** Postgres + pgvector
- **Queue:** Cron jobs first; Celery or Cloud Tasks later
- **Search:** Hybrid keyword + vector search
- **AI:** Retrieval-augmented generation with citations
- **Hosting:** Vercel for frontend; Render/Fly.io/Railway/AWS for backend; Supabase/Neon for Postgres

## Repository structure

```txt
sanjuan-ai/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── CODEX_TASKS.md
├── data/
│   └── sources/
│       └── pr_sources.yml
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── ingestion/
│   ├── retrieval/
│   └── shared/
└── scripts/
