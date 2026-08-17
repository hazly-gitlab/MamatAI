from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.database_models import User
from app.models.schemas import UserCreate, UserResponse, TokenResponse
from app.security.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result_user = await db.execute(select(User).where(User.username == user_in.username))
    if result_user.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    result_email = await db.execute(select(User).where(User.email == user_in.email))
    if result_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    result_any = await db.execute(select(User).limit(1))
    role = "admin" if not result_any.scalars().first() else user_in.role

    hashed_pass = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pass,
        role=role,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    token = create_access_token(data={"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }
