# Hybrid RAG Local

Minimal local multi-user Hybrid RAG API built with FastAPI, Ollama, Qdrant, LangChain, and LangSmith.

This repo is API-only. The main local interface is Swagger UI at `http://127.0.0.1:8000/docs`.

There is also a lightweight separate frontend app in `frontend/` for local operator or internal-user usage.

## What It Does

- Ingests local `.txt` and `.md` files
- Uses hybrid retrieval with BM25 plus dense semantic search
- Supports `user_id` and `session_id`
- Uses LangChain for chunking, embeddings, prompting, chat, and memory objects
- Supports both local path ingest and direct file upload from the frontend
- Sends traces to LangSmith when enabled

## File Guide

- `app/main.py`: API routes
- `app/config.py`: environment config
- `app/models.py`: request and response schemas
- `app/rag_service.py`: chat and ingest orchestration
- `app/retriever.py`: hybrid retrieval
- `app/ingest.py`: file loading and indexing
- `app/prompts.py`: grounded prompt text
- `app/memory.py`: in-memory session store
- `frontend/index.html`: standalone UI shell
- `frontend/styles.css`: UI styling
- `frontend/app.js`: frontend API wiring
- `requirements.txt`: dependencies
- `.env.example`: example config

## Local Run

1. Pull models:

```bash
ollama pull qwen2.5:3b
ollama pull qwen3-embedding:0.6b
```

2. Start Qdrant:

```bash
docker run -d --name qdrant-local -p 6333:6333 qdrant/qdrant
```

3. Install packages:

```bash
cd hybrid_rag_local
conda activate myenv
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and set values.

5. Start the API:

```bash
uvicorn app.main:app --reload
```

6. Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Frontend UI

Run the separate frontend from the `frontend/` folder with any static server.

One simple option:

```bash
cd frontend
python -m http.server 3000
```

Then open:

- `http://127.0.0.1:3000`

The UI calls the backend at `http://127.0.0.1:8000` by default, and you can change that in the page.

You can either:

- upload a `.txt` or `.md` file directly from the UI
- ingest by local file path

## Quick Test

For `POST /ingest`:

```json
{
  "file_path": "D:/Hybrid/hybrid_rag_local/README.md",
  "user_id": "alice"
}
```

There is also a browser upload flow backed by `POST /ingest/upload`.

For `POST /chat`:

```json
{
  "user_id": "alice",
  "session_id": "session-1",
  "message": "What does this project support and what is intentionally missing?"
}
```

## Current Limits

- Memory is process-local and resets on restart
- PDF ingestion is not included
- No auth or persistent session store yet
- The frontend is intentionally lightweight and not a full product UI yet
- Uploaded files are stored under the app's local `uploads/` directory

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for EC2 and EKS deployment guidance.

### Step 3: Ask a question that the file can answer

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"alice\", \"session_id\": \"session-2\", \"message\": \"What does this project support and what is intentionally missing?\"}"
```

Expected behavior:

- `answer` is grounded in ingested content
- `sources` contains retrieved chunks
- `session_id` matches the request

Good test queries for the sample TXT file:

- `What are the customer support hours?`
- `What is the refund policy?`
- `What is included in onboarding?`
- `Does onboarding include custom frontend development?`
- `Which file types are supported in the starter deployment?`
- `Is PDF support enabled?`
- `How is user data isolated?`
- `What happens to chat history when the API restarts?`
- `When is LangSmith tracing enabled?`
- `What are Qdrant and Ollama used for in this system?`

Example chat body for the sample TXT file:

```json
{
  "user_id": "alice",
  "session_id": "sample-session-1",
  "message": "What is included in onboarding and what is excluded?"
}
```

You can do this either from Swagger UI or with raw HTTP.

### Step 4: Verify multi-user isolation behavior

If you ingest a document with `user_id: alice`, then chat with `user_id: bob`, Bob should not retrieve Alice-scoped chunks.

Recommended manual check:

1. Ingest a user-scoped file as `alice`
2. Ask a question as `alice` and confirm relevant sources are returned
3. Ask the same question as `bob` and confirm the answer no longer relies on Alice's private chunks

### Step 5: Verify LangSmith traces

Open LangSmith Web and check project `hybrid-rag-local`.

You should see runs such as:

- `ingest_documents`
- `load_and_chunk_document`
- `embed_texts`
- `hybrid_retrieve`
- `dense_retrieve`
- `sparse_retrieve`
- `generate_grounded_answer`

If traces do not appear, check:

- `LANGSMITH_API_KEY` is set
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT=hybrid-rag-local`
- The API process was started after `.env` was updated

## 9. Debugging Checklist

If ingest fails:

- Confirm the file exists and is `.txt` or `.md`
- Confirm Ollama is running
- Confirm the embedding model named in `.env` exists in `ollama list`
- Confirm Qdrant is reachable on port `6333`

If chat fails:

- Confirm the LLM model named in `.env` exists in `ollama list`
- Confirm at least one document was ingested
- Confirm the same `user_id` is used when testing user-scoped retrieval

If retrieval looks weak:

- Start with small, factual source documents
- Ask questions that directly match document wording first
- Remember the sparse path here is BM25 over the locally visible text corpus, but it is still computed in-process rather than from a dedicated persistent sparse index

## Notes

- Supported ingestion formats in this minimal version: `.txt`, `.md`
- PDF ingestion is intentionally not included to keep dependencies and code small
- Retrieval now combines BM25 sparse search with dense semantic search
- If you ingest with `user_id`, chat requests with the same `user_id` will retrieve that scoped content
- Chat history is still in memory only and resets when the process restarts
- This code is a strong local and starter API base, but real EC2 or EKS deployment still needs persistent memory, auth, packaging, and ops hardening