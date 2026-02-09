"""Модели SQLAlchemy для базы данных.

Этот модуль определяет:
- User: Модель пользователя
- Order: Модель заказа
- OrderStatus: Энумерация статусов заказа
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer, String, ForeignKey, DateTime, JSON, Numeric, func
from sqlalchemy_utils import EmailType
from sqlalchemy.dialects.postgresql import UUID


class OrderStatus(enum.Enum):
    """Enum для описания возможных статусов заказа."""
    PENDING = "PENDING"  # Ожидание обработки
    PAID = "PAID"  # Оплачен
    SHIPPED = "SHIPPED"  # Отгружен
    CANCELED = "CANCELED"  # Отменен


class Base(DeclarativeBase):
    """Base class для всех SQLAlchemy моделей."""
    pass


class User(Base):
    """Modель пользователя.
    
    Attributes:
        id: Первичный ключ, автоинкрементируемый
        email: Уникальный электронный адрес
        hashed_password: Кэшированный пароль
        orders: Отношение к заказам пользователя
    """
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(EmailType, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    # Отношение к заказам: при удалении пользователя удалиются все его заказы
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Order(Base):
    """Modель заказа.
    
    Attributes:
        id: UUID первичный ключ, генерируемый автоматически
        user_id: ID пользователя, владельца заказа
        items: JSON данные о товарах в заказе
        total_price: Общая стоимость заказа
        status: Нынешний статус заказа
        created_at: Время создания заказа (в UTC)
        user: Отношение к User
    """
    __tablename__ = 'orders'
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Внешний ключ к таблице users с каскадным удалением
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    items: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    # Время создания с автоматическим сохранением текущего времени UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.timezone('UTC', func.now()),
        nullable=False,
        )
    user: Mapped["User"] = relationship("User", back_populates="orders")