from uuid import UUID
import json

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi.encoders import jsonable_encoder

from app.schemas import OrderCreate, OrdersResponse, OrderOut, OrderUpdate
from app.security import get_id_current_user, limiter
from app.database.database import get_async_session, get_redis
from app.repositories.orders import OrdersRepository
from app import producer


order_router = APIRouter(tags=['Orders'])


@order_router.post("/orders/", summary='Сreating an order', response_model=dict)
@limiter.limit("5/minute")
async def create_order(
    request: Request,
    order: OrderCreate, 
    current_user_id: int = Depends(get_id_current_user), 
    session: AsyncSession = Depends(get_async_session)
    ):
    db_order_id = await OrdersRepository.create_order(session, order, current_user_id)
    await producer.publish_new_order(str(db_order_id))
    return {"status": "Order created successfully", "order_id": db_order_id}


@order_router.get("/orders/{order_id}/", summary='Get order by ID', response_model=OrderOut)
@limiter.limit("10/minute")
async def get_order_by_id(
    request: Request,
    order_id: UUID,
    current_user_id: int = Depends(get_id_current_user),
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis)
    ):
    cache_key = f"order:{order_id}"
    cached_order = await redis.get(cache_key)
    if cached_order:
        return json.loads(cached_order)
    order = await OrdersRepository.get_order_by_id(session, order_id, current_user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_schema = OrderOut.model_validate(order)
    encoded = jsonable_encoder(order_schema)
    await redis.set(cache_key, json.dumps(encoded), ex=300)
    return order_schema


@order_router.patch("/orders/{order_id}/", summary='Update status order by ID', response_model=OrderOut)
@limiter.limit("5/minute")
async def update_order_endpoint(
    request: Request,
    order_id: UUID, 
    order_update: OrderUpdate, 
    current_user_id: int = Depends(get_id_current_user),
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis)
    ):
    db_order = await OrdersRepository.update_order(session, order_id, order_update, current_user_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    cache_key = f"order:{order_id}"
    order_schema = OrderOut.model_validate(db_order)
    encoded = jsonable_encoder(order_schema)
    await redis.set(cache_key, json.dumps(encoded), ex=300)
    return order_schema
    

@order_router.get(
        "/orders/user/{user_id}", 
        summary='Get all orders for the user', 
        response_model=OrdersResponse
        )
@limiter.limit("10/minute")
async def get_orders_user(
    request: Request,
    user_id: int = Depends(get_id_current_user),
    session: AsyncSession = Depends(get_async_session)
    ):
    orders = await OrdersRepository.get_orders_by_user_id(session, user_id)
    return {"orders": orders}