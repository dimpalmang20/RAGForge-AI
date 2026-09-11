# 🤖 RAGForge AI

> **A Local-First Hybrid Retrieval-Augmented Generation (RAG) Application powered by Qwen, Ollama, LangChain, Qdrant, FastAPI, and BM25.**

RAGForge AI is an end-to-end **Generative AI and Retrieval-Augmented Generation application** that allows users to upload documents and ask questions based on their content.

Instead of depending only on the pretrained knowledge of an LLM, RAGForge AI retrieves relevant information from the user's documents and provides that context to a local Large Language Model before generating the final answer.

The project demonstrates a complete local RAG pipeline including:

**Document Ingestion → Chunking → Embeddings → Vector Storage → Hybrid Retrieval → Context Augmentation → LLM Generation**

---

## 🖥️ Application Preview

![RAGForge AI Application](assets/ragforge-ai-ui.png)

### RAGForge AI Workspace

The application provides a simple workspace where users can:

- Upload knowledge documents
- Build a local knowledge base
- Ask questions about uploaded documents
- Continue conversations using session memory
- Retrieve grounded answers from indexed documents
- Reset user knowledge
- Reset conversation memory
- Monitor backend API health

---

# 📌 Introduction

Large Language Models can generate impressive answers, but they do not automatically know the contents of a user's private or newly uploaded documents.

RAG solves this problem by retrieving relevant information from an external knowledge source and providing that information to the LLM as context.

RAGForge AI implements this concept locally using:

- **Qwen** as the LLM
- **Ollama** for local model execution
- **Qwen3 Embedding** for vector embeddings
- **Qdrant** as the vector database
- **BM25** for sparse keyword retrieval
- **LangChain** for RAG orchestration
- **FastAPI** for the backend API
- **HTML, CSS and JavaScript** for the frontend
- **LangSmith** for optional tracing and observability

The entire core workflow can run locally without requiring a paid cloud LLM API.

---

# 🎯 Project Objective

The main objective of RAGForge AI is to understand and implement a practical **GenAI RAG system from end to end**.

The project focuses on understanding:

- How LLM applications work
- How embeddings represent text
- How vector databases store embeddings
- How semantic search works
- How BM25 keyword retrieval works
- How hybrid retrieval combines different retrieval strategies
- How LangChain orchestrates an RAG pipeline
- How local LLMs can be served using Ollama
- How Qwen can be used as an open/local LLM
- How conversation memory works
- How multi-user document isolation can be implemented
- How LangSmith can be used for observability

---

# ✨ Key Features

| **Feature** | **Details** |
|---|---|
| **Hybrid Retrieval** | BM25 sparse retrieval + dense semantic search merged at query time |
| **Local LLM** | Ollama running a local Qwen model for answer generation |
| **Local Embeddings** | Qwen3 Embedding model running through Ollama |
| **Vector Store** | Qdrant running locally through Docker |
| **RAG Pipeline** | Retrieves relevant document context before generating an answer |
| **Multi-User Scoping** | Documents and retrieval are isolated using `user_id` |
| **Session Memory** | Conversation history is maintained using `session_id` |
| **File Ingestion** | Supports `.txt` and `.md` document uploads |
| **Browser Upload** | Documents can be uploaded directly from the frontend |
| **Grounded Answers** | Answers are generated using retrieved document context |
| **LangChain** | Used for chunking, embeddings, prompting and LLM integration |
| **LangSmith** | Optional tracing and observability |
| **FastAPI** | REST API backend with Swagger/OpenAPI documentation |
| **Frontend** | Lightweight browser-based user interface |
| **Local-First** | Core LLM and embedding inference can run locally |

---

# 🧠 How RAGForge AI Works

```text
                    USER
                     │
                     ▼
            ┌─────────────────┐
            │  Web Frontend   │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │    FastAPI      │
            │     Backend     │
            └────────┬────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
     Upload File            User Question
          │                     │
          ▼                     ▼
    Load Document         Hybrid Retrieval
          │               ┌─────┴─────┐
          ▼               │           │
    Text Chunking        BM25      Dense Search
          │               │           │
          ▼               └─────┬─────┘
    Qwen Embeddings              │
          │                      ▼
          ▼               Relevant Context
       Qdrant                     │
          │                       ▼
          └──────────────►  LangChain Prompt
                                  │
                                  ▼
                           Ollama + Qwen
                                  │
                                  ▼
                          Grounded Answer
                                  │
                                  ▼
                                USER
                                🛠️ Requirements
Python 3.10+
Ollama
Docker Desktop
Git
VS Code
📦 Installation
1. Clone Repository
git clone https://github.com/dimpalmang20/RAGForge-AI.git
cd RAGForge-AI
2. Create Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1
3. Install Dependencies
cd hybrid_rag_local
python -m pip install -r requirements.txt
4. Install Ollama Models
ollama pull qwen2.5:7b
ollama pull qwen3-embedding:0.6b

Check:

ollama list
5. Start Qdrant
docker run -d --name qdrant-local -p 6333:6333 qdrant/qdrant

Check:

docker ps
⚙️ Environment Configuration

Create .env inside hybrid_rag_local/:

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=qwen3-embedding:0.6b
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=hybrid_rag_local
LANGSMITH_API_KEY=
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=RAGForge-AI
TOP_K=5
RERANK_TOP_K=0
▶️ Run Backend

From:

RAGForge-AI/hybrid_rag_local

run:

python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Swagger API:

http://127.0.0.1:8000/docs

Health Check:

http://127.0.0.1:8000/health
🌐 Run Frontend

Open a second terminal:

cd "C:\Users\Dimpal\RAGForge AI\hybrid_rag_local\frontend"
python -m http.server 3000

Open:

http://127.0.0.1:3000
🧑‍💻 How It Works
Upload Document
      ↓
Text Chunking
      ↓
Qwen Embeddings
      ↓
Qdrant
      ↓
User Question
      ↓
BM25 + Dense Search
      ↓
Relevant Context
      ↓
LangChain
      ↓
Qwen via Ollama
      ↓
Grounded Answer
💬 Example

Upload a document containing:

Customers can request a refund within 30 days.

Ask:

How many days do I have to request a refund?

RAGForge AI retrieves the relevant document context and Qwen generates the answer.

📌 Supported Files
.txt
.md
👨‍💻 Author

Dimpal

GitHub: https://github.com/dimpalmang20

Project: https://github.com/dimpalmang20/RAGForge-AI