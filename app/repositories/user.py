from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.model import User


class UserRepository:

    @staticmethod
    async def check_for_user_existence(session: AsyncSession, mail: str) -> Optional[int]:
        result = await session.execute(select(User.id).filter_by(email=mail))
        return result.scalar_one_or_none() 
    
    @staticmethod
    async def adding_user(session: AsyncSession, mail: str, hashed_password: str) -> None:
        new_user = User(email=mail, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, mail: str) -> Optional[User]:
        result = await session.execute(select(User).filter_by(email=mail))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def checking_user_id(session: AsyncSession, id: int) -> Optional[int]:
        result = await session.execute(select(User.id).filter_by(id=id))
        return result.scalar_one_or_none()