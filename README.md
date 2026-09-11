# Hybrid RAG Local

A minimal, self-hosted **Hybrid Retrieval-Augmented Generation** stack running entirely on your machine.  
Combines BM25 sparse search with dense semantic search, multi-user document scoping, session memory, and optional LangSmith tracing — all over a FastAPI backend with a lightweight browser UI.

---

## Repo Structure

```
Hybrid/
├── hybrid_rag_local/       # Core application
│   ├── app/
│   │   ├── main.py         # FastAPI routes
│   │   ├── config.py       # Environment settings
│   │   ├── models.py       # Request / response schemas
│   │   ├── rag_service.py  # Chat and ingest orchestration
│   │   ├── retriever.py    # BM25 + dense hybrid retrieval
│   │   ├── ingest.py       # File loading and indexing
│   │   ├── prompts.py      # Grounded prompt templates
│   │   └── memory.py       # In-process session store
│   ├── frontend/
│   │   ├── index.html      # Browser UI shell
│   │   ├── styles.css      # UI styling
│   │   └── app.js          # Frontend API wiring
│   ├── uploads/            # Uploaded files (runtime)
│   ├── requirements.txt
│   ├── README.md           # Detailed usage and API guide
│   └── DEPLOYMENT.md       # EC2 and EKS deployment guide
├── customer_support_policy.txt   # Sample ingest document
└── mini_rag_test.txt             # Minimal test document
```

---

## Key Features

| Feature | Detail |
|---|---|
| **Hybrid retrieval** | BM25 (rank-bm25) + dense semantic search merged at query time |
| **Local LLM** | Ollama — default model `qwen2.5:3b`, swap via `.env` |
| **Local embeddings** | Ollama embedding model — default `qwen3-embedding:0.6b` |
| **Vector store** | Qdrant running in Docker |
| **Multi-user scoping** | Documents and retrieval are isolated by `user_id` |
| **Session memory** | Per-session chat history via `session_id` (in-process) |
| **File ingest** | `.txt` and `.md` via path or browser upload |
| **Tracing** | LangSmith traces when `LANGSMITH_TRACING=true` |
| **Frontend** | Standalone static UI served separately on port 3000 |

---

## Stack

- **FastAPI** — API framework
- **Ollama** — local LLM and embedding inference
- **Qdrant** — vector store (Docker)
- **LangChain** — chunking, embeddings, prompting, memory
- **rank-bm25** — sparse BM25 retrieval
- **LangSmith** — optional observability and tracing

---

## Quickstart

### Prerequisites

- [Ollama](https://ollama.com) installed and running
- Docker installed
- Python 3.10+ with conda or venv

### 1. Pull models

```bash
ollama pull qwen2.5:3b
ollama pull qwen3-embedding:0.6b
```

### 2. Start Qdrant

```bash
docker run -d --name qdrant-local -p 6333:6333 qdrant/qdrant
```

### 3. Install dependencies

```bash
cd hybrid_rag_local
conda activate myenv
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# edit .env with your model names and optional LangSmith key
```

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

API docs at `http://127.0.0.1:8000/docs`

### 6. Start the frontend (optional)

```bash
cd frontend
python -m http.server 3000
```

Open `http://127.0.0.1:3000`

---

## Quick API Test

**Ingest a document:**

```json
POST /ingest
{
  "file_path": "D:/Hybrid/mini_rag_test.txt",
  "user_id": "alice"
}
```

**Ask a question:**

```json
POST /chat
{
  "user_id": "alice",
  "session_id": "session-1",
  "message": "What does this document cover?"
}
```

---

## Current Limitations

- Session memory is in-process and resets on restart
- No authentication or persistent session store
- Supported ingest formats: `.txt` and `.md` only (no PDF)
- Frontend is a lightweight internal tool, not a production UI

---

## Deployment

See [hybrid_rag_local/DEPLOYMENT.md](hybrid_rag_local/DEPLOYMENT.md) for EC2 and EKS deployment guidance.

---

## Repo Name Suggestions

| Name | Why |
|---|---|
| `hybrid-rag-local` | Direct, accurate, searchable |
| `local-rag-stack` | Emphasizes the full self-hosted stack |
| `rag-fusion-local` | Highlights the BM25 + dense fusion angle |
| `ollama-rag-api` | Tech-stack-forward, Ollama is the key differentiator |
| `multiuser-rag` | Emphasizes the user-scoped isolation feature |
| `bm25-dense-rag` | Precise — names the two retrieval methods |

**Recommended:** `hybrid-rag-local` — clean, Google-friendly, matches the codebase naming, and signals both the hybrid retrieval approach and local-first design.
