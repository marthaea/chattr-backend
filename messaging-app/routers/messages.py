from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
import json

from database import get_db, AsyncSessionLocal
from models.models import User, Message, Participant
from schemas import MessageCreate, MessageOut
from auth import get_current_user
from ws_manager import manager

router = APIRouter(tags=["Messages"])


async def _assert_participant(user_id: int, conversation_id: int, db: AsyncSession):
    result = await db.execute(
        select(Participant).where(
            Participant.user_id == user_id,
            Participant.conversation_id == conversation_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a participant of this conversation")


def _build_message_out(msg: Message, sender: User) -> MessageOut:
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender_username=sender.username,
        sender_avatar=sender.avatar_url,
        content=msg.content,
        message_type=msg.message_type,
        file_name=msg.file_name,
        file_size=msg.file_size,
        sent_at=msg.sent_at,
        is_read=msg.is_read,
    )


@router.get("/{conversation_id}", response_model=List[MessageOut])
async def get_messages(
    conversation_id: int,
    limit: int = Query(50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_participant(current_user.id, conversation_id, db)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.desc())
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()

    out = []
    for msg in reversed(messages):
        sender_result = await db.execute(select(User).where(User.id == msg.sender_id))
        sender = sender_result.scalar_one()
        out.append(_build_message_out(msg, sender))
    return out


@router.post("/", response_model=MessageOut, status_code=201)
async def send_message(
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_participant(current_user.id, body.conversation_id, db)

    msg = Message(
        conversation_id=body.conversation_id,
        sender_id=current_user.id,
        content=body.content,
        message_type=body.message_type,
        file_name=body.file_name,
        file_size=body.file_size,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    out = _build_message_out(msg, current_user)
    await manager.broadcast(body.conversation_id, out.model_dump_json())
    return out


@router.patch("/{conversation_id}/read")
async def mark_as_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_participant(current_user.id, conversation_id, db)
    await db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != current_user.id,
            Message.is_read == False,  # noqa
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}


# ── WebSocket ─────────────────────────────────────────────
@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: int,
    token: str = Query(...),
):
    from jose import jwt, JWTError
    import os

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError):
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Participant).where(
                Participant.user_id == user_id,
                Participant.conversation_id == conversation_id,
            )
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=4003)
            return

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            await websocket.close(code=4001)
            return

    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload_data = json.loads(data)
                content = payload_data.get("content", "").strip()
                message_type = payload_data.get("message_type", "text")
                file_name = payload_data.get("file_name")
                file_size = payload_data.get("file_size")
                if not content:
                    continue
            except json.JSONDecodeError:
                continue

            async with AsyncSessionLocal() as db:
                msg = Message(
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    content=content,
                    message_type=message_type,
                    file_name=file_name,
                    file_size=file_size,
                )
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

                out = _build_message_out(msg, user)
                await manager.broadcast(conversation_id, out.model_dump_json())

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
