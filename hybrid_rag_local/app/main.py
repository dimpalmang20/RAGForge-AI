from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import ChatRequest, ChatResponse, IngestRequest, ResetKnowledgeBaseRequest, ResetMemoryRequest
from app.rag_service import chat, ingest_documents, reset_session_memory, reset_user_knowledge_base


app = FastAPI(title="Hybrid RAG Local", version="0.1.0")
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "name": "hybrid-rag-local",
        "status": "ok",
        "endpoints": ["/health", "/ingest", "/ingest/upload", "/chat", "/memory/reset", "/knowledge/reset"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.post("/ingest")
def ingest_endpoint(request: IngestRequest) -> dict:
    try:
        count = ingest_documents(file_path=request.file_path, user_id=request.user_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc
    return {"status": "ingested", "chunks_ingested": count}


@app.post("/ingest/upload")
async def ingest_upload_endpoint(file: UploadFile = File(...), user_id: str | None = Form(default=None)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")

    safe_name = Path(file.filename or "uploaded.txt").name
    stored_path = UPLOAD_DIR / f"{uuid4().hex}_{safe_name}"

    try:
        content = await file.read()
        stored_path.write_bytes(content)
        count = ingest_documents(file_path=str(stored_path), user_id=user_id, source_name_override=safe_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload ingest failed: {exc}") from exc
    finally:
        await file.close()

    return {
        "status": "ingested",
        "chunks_ingested": count,
        "stored_file_path": str(stored_path),
        "original_filename": safe_name,
    }


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        return chat(user_id=request.user_id, session_id=request.session_id, message=request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc


@app.post("/memory/reset")
def reset_memory_endpoint(request: ResetMemoryRequest) -> dict:
    try:
        return reset_session_memory(user_id=request.user_id, session_id=request.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Memory reset failed: {exc}") from exc


@app.post("/knowledge/reset")
def reset_knowledge_endpoint(request: ResetKnowledgeBaseRequest) -> dict:
    try:
        return reset_user_knowledge_base(user_id=request.user_id, source=request.source)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge reset failed: {exc}") from exc