"""Share Pydantic schemas"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ShareBase(BaseModel):
    """공유 설정 기본 스키마"""
    resource_type: Literal["project", "document", "chat_room"]
    resource_id: str
    target_type: Literal["user", "project", "department"]
    target_id: str
    role: Literal["owner", "member", "viewer"]


class ShareCreate(ShareBase):
    """공유 설정 생성 요청"""
    pass


class ShareUpdate(BaseModel):
    """공유 설정 수정 요청"""
    role: Literal["owner", "member", "viewer"]


class ShareResponse(ShareBase):
    """공유 설정 응답"""
    id: str
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class ShareWithDetails(ShareResponse):
    """공유 설정 응답 (상세 정보 포함)"""
    target_name: str | None = None
    target_email: str | None = None
    creator_name: str | None = None
