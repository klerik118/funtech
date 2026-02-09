"""Репозиторий для работы с пользователями в базе данных.

Этот модуль содержит все CRUD операции для модели User.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.model import User


class UserRepository:
    """Репозиторий для управления пользователями."""

    @staticmethod
    async def check_for_user_existence(session: AsyncSession, mail: str) -> Optional[int]:
        """Проверить существование пользователя по электронной почте.
        
        Args:
            session: Асинхронная сессия БД
            mail: Электронный адрес для поиска
            
        Returns:
            int: ID пользователя если найден или None
        """
        result = await session.execute(select(User.id).filter_by(email=mail))
        return result.scalar_one_or_none() 
    
    @staticmethod
    async def adding_user(session: AsyncSession, mail: str, hashed_password: str) -> None:
        """Добавить нового пользователя в БД.
        
        Args:
            session: Асинхронная сессия БД
            mail: Электронный адрес пользователя
            hashed_password: Зашифрованный пароль
        """
        new_user = User(email=mail, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, mail: str) -> Optional[User]:
        """Получить пользователя по электронной почте.
        
        Args:
            session: Асинхронная сессия БД
            mail: Электронный адрес для поиска
            
        Returns:
            User: Объект пользователя или None если не найден
        """
        result = await session.execute(select(User).filter_by(email=mail))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def checking_user_id(session: AsyncSession, id: int) -> Optional[int]:
        """Проверить существование пользователя по ID.
        
        Args:
            session: Асинхронная сессия БД
            id: ID пользователя для проверки
            
        Returns:
            int: ID пользователя если найден или None
        """
        result = await session.execute(select(User.id).filter_by(id=id))
        return result.scalar_one_or_none()