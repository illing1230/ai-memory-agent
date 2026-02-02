"""문서 API 라우터"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import aiosqlite

from src.shared.database import get_db
from src.shared.auth import get_current_user_id
from src.document.service import DocumentService
from src.document.schemas import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentLinkResponse,
)

router = APIRouter()


def get_document_service(
    db: aiosqlite.Connection = Depends(get_db),
) -> DocumentService:
    return DocumentService(db)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chat_room_id: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service),
):
    """문서 업로드 (PDF, TXT)"""
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB 제한
        raise HTTPException(status_code=400, detail="파일 크기는 50MB 이하만 가능합니다")

    try:
        return await service.upload_document(
            file_content=content,
            filename=file.filename or "untitled",
            owner_id=user_id,
            chat_room_id=chat_room_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    chat_room_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service),
):
    """문서 목록 (내 문서 또는 대화방별)"""
    return await service.list_documents(
        owner_id=user_id, chat_room_id=chat_room_id
    )


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(
    doc_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """문서 상세 (청크 포함)"""
    try:
        return await service.get_document_detail(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service),
):
    """문서 삭제 (소유자만)"""
    try:
        await service.delete_document(doc_id, user_id)
        return {"message": "문서가 삭제되었습니다"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{doc_id}/link/{room_id}", response_model=DocumentLinkResponse)
async def link_document_to_room(
    doc_id: str,
    room_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentService = Depends(get_document_service),
):
    """문서를 대화방에 연결"""
    try:
        return await service.link_to_room(doc_id, room_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{doc_id}/link/{room_id}")
async def unlink_document_from_room(
    doc_id: str,
    room_id: str,
    service: DocumentService = Depends(get_document_service),
):
    """문서-대화방 연결 해제"""
    await service.unlink_from_room(doc_id, room_id)
    return {"message": "연결이 해제되었습니다"}
