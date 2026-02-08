from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.model import Order
from app.schemas import OrderCreate, OrderUpdate


class OrdersRepository:

    @staticmethod
    async def create_order(session: AsyncSession, order: OrderCreate, user_id: int):
        db_order = Order(user_id=user_id, items=order.items, total_price=order.total_price)
        session.add(db_order)
        await session.commit()
        await session.refresh(db_order)
        return db_order.id

    @staticmethod
    async def get_orders_by_user_id(session: AsyncSession, user_id: int) -> Optional[list]:
        result = await session.execute(select(Order).filter_by(user_id=user_id))
        return result.scalars().all()
    
    @staticmethod
    async def get_order_by_id(session: AsyncSession, order_id: str, user_id: int) -> Optional[Order]:
        result = await session.execute(select(Order).filter_by(id=order_id, user_id=user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_order(
        session: AsyncSession, 
        order_id: str, 
        order_update: OrderUpdate, 
        user_id: int
        ) -> Optional[Order]:
        result = await session.execute(select(Order).filter_by(id=order_id, user_id=user_id))
        db_order = result.scalar_one_or_none()
        if not db_order:
            return None
        db_order.status = order_update.status
        await session.commit()
        await session.refresh(db_order)
        return db_order
