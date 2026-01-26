"""Permission Pydantic 스키마"""

from typing import Literal
from pydantic import BaseModel


class PermissionCheckRequest(BaseModel):
    resource_type: Literal["memory", "chat_room", "project"]
    resource_id: str
    action: Literal["read", "update", "delete"] = "read"


class PermissionCheckResponse(BaseModel):
    allowed: bool
    resource_type: str
    resource_id: str
    user_id: str
    reason: str | None = None
