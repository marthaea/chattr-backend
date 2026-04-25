from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ── Auth ─────────────────────────────────────────────────
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class UserPublic(BaseModel):
    """Public profile — no email exposed"""
    id: int
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Conversations ─────────────────────────────────────────
class ConversationCreate(BaseModel):
    participant_ids: List[int]
    name: Optional[str] = None

class ConversationOut(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────
class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    message_type: str = "text"    # text | image | audio | video | file
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_username: str
    sender_avatar: Optional[str] = None
    content: str
    message_type: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    sent_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}


# ── Media upload ──────────────────────────────────────────
class CloudinarySignature(BaseModel):
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
