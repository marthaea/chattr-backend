from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models.models import User, Conversation, Participant
from schemas import ConversationCreate, ConversationOut
from auth import get_current_user

router = APIRouter(tags=["Conversations"])


@router.post("/", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    all_user_ids = list(set([current_user.id] + body.participant_ids))
    is_group = len(all_user_ids) > 2

    if is_group and not body.name:
        raise HTTPException(status_code=400, detail="Group conversations require a name")

    # Validate all participants exist
    result = await db.execute(select(User).where(User.id.in_(all_user_ids)))
    found_users = result.scalars().all()
    if len(found_users) != len(all_user_ids):
        raise HTTPException(status_code=404, detail="One or more users not found")

    conversation = Conversation(name=body.name, is_group=is_group)
    db.add(conversation)
    await db.flush()  # get the ID before committing

    for uid in all_user_ids:
        db.add(Participant(user_id=uid, conversation_id=conversation.id))

    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/", response_model=List[ConversationOut])
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
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Ensure current user is a participant
    result = await db.execute(
        select(Conversation)
        .join(Participant, Participant.conversation_id == Conversation.id)
        .where(Conversation.id == conversation_id, Participant.user_id == current_user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
