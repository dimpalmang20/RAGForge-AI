from pathlib import Path

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config import settings


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def _read_text_file(file_path: str) -> tuple[str, str]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only .txt and .md files are supported in this minimal starter")
    return path.name, path.read_text(encoding="utf-8")


def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=settings.ollama_embed_model, base_url=settings.ollama_base_url)


@traceable(name="load_and_chunk_document")
def load_and_chunk_document(file_path: str, source_name_override: str | None = None) -> list[Document]:
    source_name, text = _read_text_file(file_path)
    if source_name_override:
        source_name = source_name_override
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_text(text)
    return [
        Document(page_content=chunk, metadata={"source": source_name, "chunk_id": f"chunk-{index}"})
        for index, chunk in enumerate(chunks)
        if chunk.strip()
    ]


@traceable(name="embed_texts")
def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings = get_embedding_model().embed_documents(texts)
    if not embeddings:
        raise RuntimeError("Ollama embeddings did not return any vectors")
    return embeddings


@traceable(name="ensure_collection")
def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    collections = client.get_collections().collections
    exists = any(collection.name == settings.qdrant_collection for collection in collections)
    if exists:
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qdrant_models.VectorParams(
            size=vector_size,
            distance=qdrant_models.Distance.COSINE,
        ),
    )


@traceable(name="delete_existing_source_chunks")
def delete_existing_source_chunks(client: QdrantClient, source: str, user_id: str | None) -> None:
    collections = client.get_collections().collections
    exists = any(collection.name == settings.qdrant_collection for collection in collections)
    if not exists:
        return

    point_ids: list[int] = []
    next_page = None
    while True:
        points, next_page = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=256,
            with_payload=True,
            offset=next_page,
        )
        if not points:
            break
        for point in points:
            payload = point.payload or {}
            same_source = payload.get("source") == source
            same_owner = payload.get("user_id") == user_id
            if same_source and same_owner:
                point_ids.append(point.id)
        if next_page is None:
            break

    if point_ids:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=qdrant_models.PointIdsList(points=point_ids),
        )


@traceable(name="delete_user_chunks")
def delete_user_chunks(client: QdrantClient, user_id: str, source: str | None = None) -> int:
    collections = client.get_collections().collections
    exists = any(collection.name == settings.qdrant_collection for collection in collections)
    if not exists:
        return 0

    point_ids: list[int] = []
    next_page = None
    while True:
        points, next_page = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=256,
            with_payload=True,
            offset=next_page,
        )
        if not points:
            break
        for point in points:
            payload = point.payload or {}
            same_owner = payload.get("user_id") == user_id
            same_source = source is None or payload.get("source") == source
            if same_owner and same_source:
                point_ids.append(point.id)
        if next_page is None:
            break

    if point_ids:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=qdrant_models.PointIdsList(points=point_ids),
        )
    return len(point_ids)


@traceable(name="upsert_document_chunks")
def upsert_document_chunks(client: QdrantClient, chunks: list[Document], user_id: str | None = None) -> int:
    if not chunks:
        return 0

    embeddings = embed_texts([chunk.page_content for chunk in chunks])
    ensure_collection(client, len(embeddings[0]))
    source_name = chunks[0].metadata.get("source", "unknown")
    delete_existing_source_chunks(client, source=source_name, user_id=user_id)

    points: list[qdrant_models.PointStruct] = []
    for index, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True)):
        source = chunk.metadata.get("source", "unknown")
        chunk_id = chunk.metadata.get("chunk_id", f"chunk-{index}")
        point_id = abs(hash(f"{source}:{chunk_id}:{index}:{user_id or 'global'}"))
        payload = {
            "source": source,
            "chunk_id": chunk_id,
            "text": chunk.page_content,
            "user_id": user_id,
        }
        points.append(qdrant_models.PointStruct(id=point_id, vector=vector, payload=payload))

    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)