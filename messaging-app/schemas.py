from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ── Auth ────────────────────────────────────────────────
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
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Conversations ────────────────────────────────────────
class ConversationCreate(BaseModel):
    participant_ids: List[int]   # IDs of OTHER users to add
    name: Optional[str] = None   # required for group chats

class ConversationOut(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Messages ─────────────────────────────────────────────
class MessageCreate(BaseModel):
    conversation_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_username: str
    content: str
    sent_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}
