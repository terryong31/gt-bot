from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


# Invite Codes
class InviteCreate(BaseModel):
    name: str
    phone: Optional[str] = None


class InviteResponse(BaseModel):
    id: int
    code: str
    name: str
    phone: Optional[str]
    telegram_id: Optional[int]
    is_used: bool
    created_at: datetime
    used_at: Optional[datetime]

    class Config:
        from_attributes = True


# Users
class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_allowed: bool
    last_activity: Optional[datetime]
    created_at: Optional[datetime] = None
    invite_name: Optional[str] = None
    is_google_connected: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    is_allowed: Optional[bool] = None


# Chat Logs
class ChatLogResponse(BaseModel):
    id: int
    user_id: int
    message_type: str
    content: Optional[str]
    file_name: Optional[str]
    bot_response: Optional[str]
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedLogs(BaseModel):
    items: List[ChatLogResponse]
    total: int
    page: int
    limit: int
    pages: int
