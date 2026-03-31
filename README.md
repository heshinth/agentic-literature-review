# Agentic Literature Review

Full-stack app for automated literature review generation.
Enter a topic, and the system searches papers, processes PDFs, retrieves relevant chunks, and produces a markdown summary.

## What It Does

1. Generate search queries from a topic.
2. Fetch and rank papers.
3. Download and extract PDF text.
4. Build sparse embeddings and store in Qdrant.
5. Run agentic retrieval.
6. Return a citation-style markdown report.

## Stack

- Frontend: Nuxt 4
- Backend: FastAPI
- Database: PostgreSQL
- Vector DB: Qdrant
- LLM: Groq API
- Paper source: Semantic Scholar API

## Quick Start (Docker)

1. Create `.env` in the repo root:

```bash
cp backend/.env.sample .env
```

2. Set required keys in `.env`:

```env
S2_API_KEY=your_semantic_scholar_key
GROQ_API_KEY=your_groq_key
```

3. Start everything:

```bash
docker compose up --build
```

4. Open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Postgres UI (pgweb): http://localhost:8081

## Local Development (Optional)

Run only data services:

```bash
docker compose up -d postgres qdrant
```

Backend:

```bash
cd backend
cp .env.sample .env
uv sync
uv run uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## API

Base URL: `http://localhost:8000`

- `GET /health`
- `POST /research` (SSE stream)

```bash
curl -N -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic":"latest developments in large language models"}'
```

## Key Environment Variables

- Required: `S2_API_KEY`, `GROQ_API_KEY`
- Database: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- Vector store: `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_BATCH_SIZE`
- Pipeline toggles: `RUN_EMBEDDING_STEP`, `RUN_QDRANT_STEP`

Full list: `backend/.env.sample`

## Outputs

- Summaries: `backend/outputs/`
- Logs/artifacts: `backend/logs/`
- Downloaded PDFs: `backend/temp_pdfs/`

## License

MIT (see `LICENSE`).