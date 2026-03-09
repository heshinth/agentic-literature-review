# Agentic Literature Review — API Documentation

Base URL: `http://localhost:8000`  
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## Endpoints

### `GET /health`

Health check. Returns immediately with no dependencies.

**Response `200 OK`**
```json
{ "status": "ok" }
```

**Example**
```bash
curl http://localhost:8000/health
```

---

### `POST /research`

Run a full literature review pipeline for a given research topic.  
Returns a **Server-Sent Events (SSE)** stream that emits progress updates in real time, followed by the final markdown result when done.

**Request body**
```json
{ "topic": "string (min 3 chars)" }
```

| Field   | Type   | Required | Description                         |
|---------|--------|----------|-------------------------------------|
| `topic` | string | ✅       | Research topic, at least 3 characters |

**Response**

- Content-Type: `text/event-stream`
- Each event is a line in the format: `data: {json}\n\n`
- The connection stays open until the pipeline finishes or errors.

**Example**
```bash
curl -N -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "large language models"}'
```

> `-N` disables curl buffering so events print as they arrive.

---

## SSE Event Schema

Every event is JSON with the following shape:

```json
{
  "event":   "status | result | error",
  "message": "Human-readable description",
  "step":    1,
  "total":   6,
  "data":    {}
}
```

| Field     | Type    | Present on        | Description                                     |
|-----------|---------|-------------------|-------------------------------------------------|
| `event`   | string  | always            | Event type — `status`, `result`, or `error`     |
| `message` | string  | always            | What the pipeline is currently doing            |
| `step`    | integer | status, result    | Current step number (1–6)                       |
| `total`   | integer | status, result    | Total number of steps (always 6)                |
| `data`    | object  | result only       | Contains `markdown` key with the full review    |

---

## Pipeline Steps

The pipeline emits one `status` event before each step begins.

| Step | Message                                        | What happens                                              |
|------|------------------------------------------------|-----------------------------------------------------------|
| 1    | Generating search queries...                   | LLM generates multiple search queries from the topic      |
| 2    | Searching and deduplicating papers...          | Queries Semantic Scholar API, deduplicates results        |
| 3    | Downloading and extracting N PDFs...           | Downloads open-access PDFs, extracts full text            |
| 4    | Creating sparse embeddings...                  | Chunks text, creates BM42 sparse vectors via fastembed    |
| 5    | Storing vectors in Qdrant...                   | Upserts vectors into Qdrant vector store                  |
| 6    | Running AI retrieval and generating review...  | Agentic retrieval loop + LLM generates markdown summary   |

---

## Full SSE Stream Example

```
data: {"event": "status", "message": "Generating search queries...", "step": 1, "total": 6}

data: {"event": "status", "message": "Searching and deduplicating papers...", "step": 2, "total": 6}

data: {"event": "status", "message": "Downloading and extracting 25 PDFs...", "step": 3, "total": 6}

data: {"event": "status", "message": "Creating sparse embeddings...", "step": 4, "total": 6}

data: {"event": "status", "message": "Storing vectors in Qdrant...", "step": 5, "total": 6}

data: {"event": "status", "message": "Running AI retrieval and generating review...", "step": 6, "total": 6}

data: {"event": "result", "message": "Done!", "step": 6, "total": 6, "data": {"markdown": "## Literature Review\n\n..."}}
```

On error, the stream emits one `error` event and closes:
```
data: {"event": "error", "message": "Pipeline failed: <reason>"}
```

---

## Consuming SSE in JavaScript

```js
const res = await fetch('http://localhost:8000/research', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic: 'large language models' }),
});

const reader = res.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue;
    const event = JSON.parse(line.slice(6));

    if (event.event === 'status') {
      console.log(`[${event.step}/${event.total}] ${event.message}`);
    } else if (event.event === 'result') {
      console.log('Review:\n', event.data.markdown);
    } else if (event.event === 'error') {
      console.error('Error:', event.message);
    }
  }
}
```

---

## Running Locally

**Prerequisites:** Docker, Python 3.12+, `uv`

```bash
# 1. Start Postgres + Qdrant
docker compose up -d

# 2. Start the API server
fastapi run ./app/server.py
#   or in dev mode with auto-reload:
fastapi dev ./app/server.py
```

**Environment variables** (`.env` file at repo root):

| Variable               | Default          | Description                        |
|------------------------|------------------|------------------------------------|
| `DB_USER`              | —                | Postgres username                  |
| `DB_PASSWORD`          | —                | Postgres password                  |
| `DB_HOST`              | —                | Postgres host                      |
| `DB_PORT`              | —                | Postgres port                      |
| `DB_NAME`              | —                | Postgres database name             |
| `RUN_EMBEDDING_STEP`   | `1`              | Set to `0` to skip embedding step  |
| `RUN_QDRANT_STEP`      | `1`              | Set to `0` to skip Qdrant upsert   |
| `QDRANT_COLLECTION`    | `papers_sparse`  | Qdrant collection name             |
| `QDRANT_BATCH_SIZE`    | `64`             | Upsert batch size                  |
| `EMBEDDING_PREVIEW_PATH` | `logs/embedding_preview.jsonl` | Path for embedding preview log |
| `EMBEDDING_PREVIEW_COUNT` | `100`         | Number of records to preview       |
