from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.users.service import UserService


async def get_user_service(
    db_session: AsyncSession = Depends(get_async_session)
) -> UserService:
    """
    Dependency to get UserService instance
    """
    return UserService(db_session) 