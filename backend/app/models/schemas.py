from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    conversation_id: str
    sender: str
    content: str
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MemoryResponse(BaseModel):
    id: int
    content: str
    category: str
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ScheduledTaskResponse(BaseModel):
    id: int
    name: str
    command: str
    schedule: str
    status: str
    last_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
