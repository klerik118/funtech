"""Репозиторий для работы с заказами в базе данных.

Этот модуль содержит все CRUD операции для модели Order.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.model import Order
from app.schemas import OrderCreate, OrderUpdate


class OrdersRepository:
    """Репозиторий для управления заказами."""

    @staticmethod
    async def create_order(session: AsyncSession, order: OrderCreate, user_id: int):
        """Создать новый заказ.
        
        Args:
            session: Асинхронная сессия БД
            order: Данные для создания заказа
            user_id: ID пользователя, создающего заказ
            
        Returns:
            UUID: ID созданного заказа
        """
        db_order = Order(user_id=user_id, items=order.items, total_price=order.total_price)
        session.add(db_order)
        await session.commit()
        await session.refresh(db_order)
        return db_order.id

    @staticmethod
    async def get_orders_by_user_id(session: AsyncSession, user_id: int) -> Optional[list]:
        """Получить все заказы пользователя.
        
        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя
            
        Returns:
            list: Список заказов пользователя или None
        """
        result = await session.execute(select(Order).filter_by(user_id=user_id))
        return result.scalars().all()
    
    @staticmethod
    async def get_order_by_id(session: AsyncSession, order_id: str, user_id: int) -> Optional[Order]:
        """Получить заказ по ID.
        
        Args:
            session: Асинхронная сессия БД
            order_id: UUID заказа
            user_id: ID пользователя (для проверки прав доступа)
            
        Returns:
            Order: Объект заказа или None если не найден
        """
        result = await session.execute(select(Order).filter_by(id=order_id, user_id=user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_order(
        session: AsyncSession, 
        order_id: str, 
        order_update: OrderUpdate, 
        user_id: int
        ) -> Optional[Order]:
        """Обновить статус заказа.
        
        Args:
            session: Асинхронная сессия БД
            order_id: UUID заказа для обновления
            order_update: Новые данные для заказа
            user_id: ID пользователя (для проверки прав доступа)
            
        Returns:
            Order: Обновленный заказ или None если не найден
        """
        result = await session.execute(select(Order).filter_by(id=order_id, user_id=user_id))
        db_order = result.scalar_one_or_none()
        if not db_order:
            return None
        db_order.status = order_update.status
        await session.commit()
        await session.refresh(db_order)
        return db_order
