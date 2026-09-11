from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langsmith import traceable

from app.config import settings
from app.ingest import delete_user_chunks, get_qdrant_client, load_and_chunk_document, upsert_document_chunks
from app.memory import session_store
from app.models import ChatResponse, SourceChunk
from app.prompts import SYSTEM_PROMPT
from app.retriever import hybrid_retrieve


def _format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant context was retrieved."
    return "\n\n".join(
        f"[{chunk['source']}:{chunk['chunk_id']}]\n{chunk['text']}" for chunk in chunks
    )


GROUNDING_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        (
            "human",
            "Use the provided retrieval context to answer the user.\n\n"
            "Context:\n{context}\n\n"
            "User question:\n{message}",
        ),
    ]
)


CHAT_MODEL = ChatOllama(
    model=settings.ollama_llm_model,
    base_url=settings.ollama_base_url,
    temperature=0,
)


ANSWER_CHAIN = GROUNDING_PROMPT | CHAT_MODEL | StrOutputParser()


@traceable(name="generate_grounded_answer")
def generate_grounded_answer(message: str, context: str, history: list[dict[str, str]]) -> str:
    content = ANSWER_CHAIN.invoke({"message": message, "context": context, "history": history}).strip()
    if not content:
        raise RuntimeError("Ollama chat response did not include message content")
    return content


@traceable(name="ingest_documents")
def ingest_documents(file_path: str, user_id: str | None = None, source_name_override: str | None = None) -> int:
    client = get_qdrant_client()
    chunks = load_and_chunk_document(file_path, source_name_override=source_name_override)
    return upsert_document_chunks(client, chunks, user_id=user_id)


@traceable(name="chat_with_hybrid_rag")
def chat(user_id: str, session_id: str, message: str) -> ChatResponse:
    client = get_qdrant_client()
    retrieved_chunks = hybrid_retrieve(client, query=message, user_id=user_id, limit=settings.top_k)
    context = _format_context(retrieved_chunks)
    history_store = session_store.get_history(user_id=user_id, session_id=session_id)
    history = history_store.messages
    answer = generate_grounded_answer(message=message, context=context, history=history)

    history_store.add_messages([HumanMessage(content=message), AIMessage(content=answer)])
    session_store.trim_history(user_id=user_id, session_id=session_id)

    sources = [
        SourceChunk(
            source=chunk["source"],
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            score=chunk["score"],
        )
        for chunk in retrieved_chunks
    ]
    return ChatResponse(session_id=session_id, answer=answer, sources=sources)


@traceable(name="reset_session_memory")
def reset_session_memory(user_id: str, session_id: str) -> dict:
    session_store.clear_history(user_id=user_id, session_id=session_id)
    return {"status": "cleared", "scope": "session-memory", "user_id": user_id, "session_id": session_id}


@traceable(name="reset_user_knowledge_base")
def reset_user_knowledge_base(user_id: str, source: str | None = None) -> dict:
    client = get_qdrant_client()
    deleted_count = delete_user_chunks(client, user_id=user_id, source=source)
    cleared_sessions = session_store.clear_user_histories(user_id)
    return {
        "status": "cleared",
        "scope": "knowledge-base",
        "user_id": user_id,
        "source": source,
        "chunks_deleted": deleted_count,
        "sessions_cleared": cleared_sessions,
    }