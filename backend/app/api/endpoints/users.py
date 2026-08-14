from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.app.api.deps import get_db, verify_admin
from backend.app.models.models import User, UserRole
from backend.app.models.schemas import UserOut, UserUpdate, UserCreate
from backend.app.security.password import hash_password

router = APIRouter()

@router.get("/", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()

@router.post("/", response_model=UserOut)
async def create_user_by_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pwd = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=UserRole.USER,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.hashed_password = hash_password(user_in.password)

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="An administrator cannot delete their own account.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"status": "success", "message": "User deleted successfully."}
