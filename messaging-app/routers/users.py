from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models.models import User
from schemas import UserPublic, UserOut, UserUpdate
from auth import get_current_user

router = APIRouter(tags=["Users"])


@router.get("/", response_model=List[UserPublic])
async def list_users(
    search: str = Query(None, description="Search by username"),
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users (excluding yourself). Optionally search by username."""
    query = select(User).where(User.id != current_user.id)
    if search:
        query = query.where(User.username.ilike(f"%{search}%"))
    query = query.order_by(User.username).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get your own full profile."""
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update your avatar URL and/or bio."""
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    if body.bio is not None:
        current_user.bio = body.bio
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get any user's public profile by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
