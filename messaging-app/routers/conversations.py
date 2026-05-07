from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.models import User, Conversation, Participant, Message
from schemas import ConversationCreate
from auth import get_current_user

router = APIRouter(tags=["Conversations"])


class ParticipantInfo(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    model_config = {"from_attributes": True}


class ConversationRich(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime
    participants: List[ParticipantInfo]
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


@router.post("/", response_model=ConversationRich, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    all_user_ids = list(set([current_user.id] + body.participant_ids))
    is_group = len(all_user_ids) > 2

    if is_group and not body.name:
        raise HTTPException(status_code=400, detail="Group conversations require a name")

    result = await db.execute(select(User).where(User.id.in_(all_user_ids)))
    found_users = result.scalars().all()
    if len(found_users) != len(all_user_ids):
        raise HTTPException(status_code=404, detail="One or more users not found")

    conversation = Conversation(name=body.name, is_group=is_group)
    db.add(conversation)
    await db.flush()

    for uid in all_user_ids:
        db.add(Participant(user_id=uid, conversation_id=conversation.id))

    await db.commit()
    await db.refresh(conversation)
    return await _enrich(conversation, current_user.id, db)


@router.get("/", response_model=List[ConversationRich])
async def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .join(Participant, Participant.conversation_id == Conversation.id)
        .where(Participant.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()
    return [await _enrich(c, current_user.id, db) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationRich)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .join(Participant, Participant.conversation_id == Conversation.id)
        .where(Conversation.id == conversation_id, Participant.user_id == current_user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await _enrich(conversation, current_user.id, db)


async def _enrich(conversation: Conversation, current_user_id: int, db: AsyncSession) -> ConversationRich:
    # Get all participants with their info
    result = await db.execute(
        select(User)
        .join(Participant, Participant.user_id == User.id)
        .where(Participant.conversation_id == conversation.id)
    )
    all_participants = result.scalars().all()

    participant_info = [
        ParticipantInfo(id=u.id, username=u.username, avatar_url=u.avatar_url)
        for u in all_participants
    ]

    # For 1-on-1 chats, use the OTHER person's name instead of "Chat #N"
    display_name = conversation.name
    if not conversation.is_group:
        other = next((u for u in all_participants if u.id != current_user_id), None)
        if other:
            display_name = other.username

    # Get last message for preview
    last_msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.sent_at.desc())
        .limit(1)
    )
    last_msg = last_msg_result.scalar_one_or_none()

    last_message_text = None
    last_message_at = None
    if last_msg:
        if last_msg.message_type == "text":
            last_message_text = last_msg.content[:60]
        else:
            last_message_text = f"📎 {last_msg.message_type.capitalize()}"
        last_message_at = last_msg.sent_at

    return ConversationRich(
        id=conversation.id,
        name=display_name,
        is_group=conversation.is_group,
        created_at=conversation.created_at,
        participants=participant_info,
        last_message=last_message_text,
        last_message_at=last_message_at,
    )
