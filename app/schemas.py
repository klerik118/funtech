from typing import List, Dict, Annotated
from decimal import Decimal
from uuid import UUID
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    email: EmailStr = 'Введите email'
    password: str = Field('Введите пароль', min_length=5, max_length=20, pattern=r'^[a-zA-Z0-9]+$')


PositiveIntGe1 = Annotated[int, Field(ge=1)]

Price = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]

class OrderCreate(BaseModel):
    items: List[Dict[str, PositiveIntGe1]] = '[{"item_name": 1}]'
    total_price: Price = 'Введите общую стоимость заказа'


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderOut(BaseModel):
    id: UUID
    items: List[Dict[str, int]]
    total_price: float
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OrdersResponse(BaseModel):
    orders: list[OrderOut]


class OrderUpdate(BaseModel):
    status: OrderStatus