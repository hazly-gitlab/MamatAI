from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.api.deps import get_db, get_current_active_user
from backend.app.core.config import settings
from backend.app.security.jwt import create_access_token
from backend.app.security.password import hash_password, verify_password
from backend.app.models.models import User, UserRole
from backend.app.models.schemas import UserCreate, UserOut, Token

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    # Hash password
    hashed_pwd = hash_password(user_in.password)

    # Check if this is the first user; if so, make them an administrator, otherwise a user.
    users_count_res = await db.execute(select(User))
    first_user = users_count_res.scalars().first() is None
    role = UserRole.ADMINISTRATOR if first_user else UserRole.USER

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=role,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
