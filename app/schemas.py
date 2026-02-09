"""Pydantic схемы для валидации данных запросов и ответов API.

Этот модуль содержит все Pydantic модели для:
- Входных данных (заказы, регистрация пользователей)
- Выходных данных (ответы API)
- Настраиваемых типов с валидацией
"""

from typing import List, Dict, Annotated
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """Схема для регистрации нового пользователя.
    
    Attributes:
        email: Валидный электронный адрес
        password: Пароль от 5 до 20 символов, только буквы и цифры
    """
    email: EmailStr = 'Введите email'
    password: str = Field('Введите пароль', min_length=5, max_length=20, pattern=r'^[a-zA-Z0-9]+$')


# Настраиваемые типы с валидацией
PositiveIntGe1 = Annotated[int, Field(ge=1)]  # Положительное целое число >= 1

Price = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]  # Положительная цена с 2 знаками после запятой


class OrderCreate(BaseModel):
    """Схема для создания нового заказа.
    
    Attributes:
        items: Список товаров в заказе (словарь с названием и количеством)
        total_price: Общая стоимость заказа
    """
    items: List[Dict[str, PositiveIntGe1]] = '[{"item_name": 1}]'
    total_price: Price = 'Введите общую стоимость заказа'


class OrderStatus(str, Enum):
    """Enum для статусов заказа.
    
    Возможные статусы:
        - PENDING: Заказ в ожидании обработки
        - PAID: Заказ оплачен
        - SHIPPED: Заказ отправлен
        - CANCELLED: Заказ отменен
    """
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderOut(BaseModel):
    """Схема ответа для отдельного заказа.
    
    Attributes:
        id: UUID заказа
        items: Товары в заказе
        total_price: Общая стоимость
        status: Статус заказа
        created_at: Время создания заказа
    
    Config:
        from_attributes: Позволяет работать с SQLAlchemy моделями
    """
    id: UUID
    items: List[Dict[str, int]]
    total_price: float
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OrdersResponse(BaseModel):
    """Схема ответа для списка заказов.
    
    Attributes:
        orders: Список заказов
    """
    orders: list[OrderOut]


class OrderUpdate(BaseModel):
    """Схема для обновления статуса заказа.
    
    Attributes:
        status: Новый статус заказа
    """
    status: OrderStatus