import re
from collections import defaultdict

from rank_bm25 import BM25Okapi
from langsmith import traceable
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from app.config import settings
from app.ingest import get_embedding_model


TOKEN_PATTERN = re.compile(r"\b\w+\b")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _to_source_chunk(payload: dict, score: float, dense_score: float = 0.0, sparse_score: float = 0.0) -> dict:
    return {
        "id": str(payload.get("id", payload.get("chunk_id", "unknown"))),
        "source": payload.get("source", "unknown"),
        "chunk_id": payload.get("chunk_id", "chunk-unknown"),
        "text": payload.get("text", ""),
        "score": float(score),
        "dense_score": float(dense_score),
        "sparse_score": float(sparse_score),
    }


def _is_visible_to_user(payload: dict, user_id: str | None) -> bool:
    owner = payload.get("user_id")
    return owner is None or owner == user_id


@traceable(name="load_sparse_corpus")
def load_sparse_corpus(client: QdrantClient, user_id: str | None) -> list[Document]:
    documents: list[Document] = []
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
            if not _is_visible_to_user(payload, user_id):
                continue
            documents.append(
                Document(
                    page_content=payload.get("text", ""),
                    metadata={
                        "id": str(point.id),
                        "source": payload.get("source", "unknown"),
                        "chunk_id": payload.get("chunk_id", "chunk-unknown"),
                        "user_id": payload.get("user_id"),
                    },
                )
            )
        if next_page is None:
            break

    return documents


@traceable(name="dense_retrieve")
def dense_retrieve(client: QdrantClient, query: str, user_id: str | None, limit: int) -> list[dict]:
    vector = get_embedding_model().embed_query(query)
    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=max(limit * 4, 20),
        with_payload=True,
    )
    matches = response.points

    results: list[dict] = []
    for match in matches:
        payload = match.payload or {}
        if not _is_visible_to_user(payload, user_id):
            continue
        payload = {**payload, "id": str(match.id)}
        results.append(_to_source_chunk(payload, score=match.score, dense_score=match.score))
    unique: dict[str, dict] = {}
    for item in results:
        unique[item["id"]] = item
    return list(unique.values())[:limit]


@traceable(name="sparse_retrieve")
def sparse_retrieve(client: QdrantClient, query: str, user_id: str | None, limit: int) -> list[dict]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    documents = load_sparse_corpus(client, user_id)
    if not documents:
        return []

    tokenized_corpus = [_tokenize(document.page_content) for document in documents]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(range(len(documents)), key=lambda index: scores[index], reverse=True)
    collected: list[dict] = []
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            continue
        document = documents[index]
        payload = {
            "id": document.metadata.get("id", document.metadata.get("chunk_id", "unknown")),
            "source": document.metadata.get("source", "unknown"),
            "chunk_id": document.metadata.get("chunk_id", "chunk-unknown"),
            "text": document.page_content,
        }
        collected.append(_to_source_chunk(payload, score=score, sparse_score=score))
        if len(collected) >= limit:
            break
    return collected


@traceable(name="hybrid_retrieve")
def hybrid_retrieve(client: QdrantClient, query: str, user_id: str | None, limit: int | None = None) -> list[dict]:
    top_k = limit or settings.top_k
    dense_results = dense_retrieve(client, query=query, user_id=user_id, limit=top_k * 2)
    sparse_results = sparse_retrieve(client, query=query, user_id=user_id, limit=top_k * 2)

    merged: dict[str, dict] = defaultdict(dict)
    dense_max = max((item["dense_score"] for item in dense_results), default=1.0)
    sparse_max = max((item["sparse_score"] for item in sparse_results), default=1.0)

    for item in dense_results:
        merged[item["id"]] = {**item}
        merged[item["id"]]["hybrid_score"] = (item["dense_score"] / dense_max) * 0.7

    for item in sparse_results:
        if item["id"] in merged:
            merged[item["id"]]["sparse_score"] = item["sparse_score"]
            merged[item["id"]]["hybrid_score"] += (item["sparse_score"] / sparse_max) * 0.3
        else:
            merged[item["id"]] = {**item, "hybrid_score": (item["sparse_score"] / sparse_max) * 0.3}

    ranked = sorted(merged.values(), key=lambda item: item.get("hybrid_score", 0.0), reverse=True)
    for item in ranked:
        item["score"] = float(item.get("hybrid_score", 0.0))
    return ranked[:top_k]