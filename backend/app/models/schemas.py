from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import UserRole

# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class LoginRequest(BaseModel):
    username: str  # email as username for OAuth2 standard
    password: str

# Conversation Schemas
class MessageBase(BaseModel):
    role: str
    content: str

class MessageOut(MessageBase):
    id: int
    conversation_id: str
    created_at: datetime
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    attachments: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True

# Document Schemas
class DocumentOut(BaseModel):
    id: int
    filename: str
    file_size: int
    content_type: str
    status: str
    created_at: datetime
    summary: Optional[str] = None

    class Config:
        from_attributes = True

# Tool Settings Schemas
class ToolSettingOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    requires_confirmation: bool
    permission_level: str

    class Config:
        from_attributes = True

class ToolSettingUpdate(BaseModel):
    enabled: Optional[bool] = None
    requires_confirmation: Optional[bool] = None
    permission_level: Optional[str] = None

# Audit Log Schemas
class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    parameters: Optional[Dict[str, Any]] = None
    status: str
    approved_by: Optional[str] = None
    execution_time_ms: Optional[float] = None

    class Config:
        from_attributes = True

# Memory Schemas
class MemoryOut(BaseModel):
    id: int
    content: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

class MemoryCreate(BaseModel):
    content: str
    category: str = "general"

# Skill Schemas
class SkillOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    current_version: str
    risk_level: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SkillVersionOut(BaseModel):
    id: int
    skill_id: int
    version: str
    definition: Dict[str, Any]
    status: str
    created_at: datetime
    created_by: Optional[str] = None
    evaluation_score: Optional[float] = None

    class Config:
        from_attributes = True

class SkillExecutionOut(BaseModel):
    id: int
    skill_id: int
    skill_version: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    status: str
    execution_time_ms: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SkillFailureOut(BaseModel):
    id: int
    skill_execution_id: int
    error_type: str
    error_message: str
    root_cause: Optional[str] = None
    severity: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SkillImprovementOut(BaseModel):
    id: int
    skill_id: int
    old_version: str
    new_version: str
    reason: str
    evaluation_score: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class RepairJobOut(BaseModel):
    id: int
    error: str
    diagnosis: Optional[str] = None
    proposed_fix: Optional[str] = None
    sandbox_path: Optional[str] = None
    test_result: Optional[str] = None
    verification_result: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationResultOut(BaseModel):
    id: int
    skill_id: int
    version: str
    test_count: int
    passed_count: int
    failed_count: int
    score: float
    regression_detected: bool
    created_at: datetime

    class Config:
        from_attributes = True
