from typing import Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    file_path: str = Field(..., description="Local path to a .txt or .md document")
    user_id: Optional[str] = Field(default=None, description="Optional per-user document scope")


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


class SourceChunk(BaseModel):
    source: str
    chunk_id: str
    text: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceChunk]


class ResetMemoryRequest(BaseModel):
    user_id: str
    session_id: str


class ResetKnowledgeBaseRequest(BaseModel):
    user_id: str
    source: Optional[str] = None