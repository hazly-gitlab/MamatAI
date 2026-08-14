from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.core.config import settings
from backend.app.security.jwt import decode_access_token
from backend.app.models.models import User, UserRole

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    sub = decode_access_token(token)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # sub can be user email or user ID. Let's look up by email first, then by id if numeric.
    query = select(User).where((User.email == sub) | (User.id.cast(type_=User.id.type) == (int(sub) if sub.isdigit() else -1)))
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return user

# Predefined role dependencies
verify_admin = RoleChecker([UserRole.ADMINISTRATOR])
verify_user_or_above = RoleChecker([UserRole.ADMINISTRATOR, UserRole.USER])
verify_any_role = RoleChecker([UserRole.ADMINISTRATOR, UserRole.USER, UserRole.READ_ONLY])
