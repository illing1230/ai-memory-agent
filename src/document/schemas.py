"""문서 스키마"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """문서 응답"""
    id: str
    name: str
    file_type: Literal["pdf", "txt"]
    file_size: int
    owner_id: str
    chat_room_id: Optional[str] = None
    status: Literal["processing", "completed", "failed"]
    chunk_count: int = 0
    created_at: Optional[str] = None


class DocumentChunkResponse(BaseModel):
    """문서 청크 응답"""
    id: str
    document_id: str
    content: str
    chunk_index: int
    vector_id: Optional[str] = None


class DocumentDetailResponse(DocumentResponse):
    """문서 상세 응답 (청크 포함)"""
    chunks: list[DocumentChunkResponse] = []


class DocumentLinkResponse(BaseModel):
    """문서-대화방 연결 응답"""
    document_id: str
    chat_room_id: str
    linked_at: Optional[str] = None
