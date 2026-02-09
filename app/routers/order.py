"""Маршруты для управления заказами.

Этот модуль содержит все HTTP endpoints для операций с заказами:
- Создание новых заказов
- Получение информации о заказах
- Обновление статуса заказов
- Получение списка заказов пользователя

Особенности:
- Кеширование результатов в Redis (TTL: 300 сек)
- Rate limiting для защиты от злоупотреблений
- Асинхронная обработка через RabbitMQ и Celery
- JWT аутентификация для всех операций
"""

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
@limiter.limit("5/minute")  # Ограничение: максимум 5 заказов в минуту
async def create_order(
    request: Request,
    order: OrderCreate, 
    current_user_id: int = Depends(get_id_current_user), 
    session: AsyncSession = Depends(get_async_session)
    ):
    """Создать новый заказ.
    
    Создает заказ в базе данных и отправляет сообщение в RabbitMQ
    для асинхронной обработки через Celery worker.
    
    Args:
        request: Объект HTTP запроса (для rate limiting)
        order: Данные заказа (товары и общая стоимость)
        current_user_id: ID аутентифицированного пользователя
        session: Асинхронная сессия базы данных
        
    Returns:
        dict: Словарь со статусом и UUID созданного заказа
            {
                "status": "Order created successfully",
                "order_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        
    Raises:
        HTTPException 401: Пользователь не авторизован
        HTTPException 429: Превышен лимит запросов (5/минуту)
        HTTPException 422: Неверные данные заказа
        
    Note:
        - Заказ создается со статусом PENDING
        - Сообщение публикуется в очередь 'new_order' для фоновой обработки
        - Rate limit применяется на основе user_id или IP адреса
    """
    # Создаем заказ в базе данных
    db_order_id = await OrdersRepository.create_order(session, order, current_user_id)
    
    # Отправляем сообщение в RabbitMQ для асинхронной обработки
    await producer.publish_new_order(str(db_order_id))
    
    return {"status": "Order created successfully", "order_id": db_order_id}


@order_router.get("/orders/{order_id}/", summary='Get order by ID', response_model=OrderOut)
@limiter.limit("10/minute")  # Ограничение: максимум 10 запросов в минуту
async def get_order_by_id(
    request: Request,
    order_id: UUID,
    current_user_id: int = Depends(get_id_current_user),
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis)
    ):
    """Получить информацию о заказе по ID с кешированием.
    
    Сначала проверяет наличие заказа в кеше Redis. Если заказ не найден
    в кеше, загружает его из базы данных и сохраняет в кеш на 5 минут.
    Пользователь может получить только свои собственные заказы.
    
    Args:
        request: Объект HTTP запроса (для rate limiting)
        order_id: UUID заказа для поиска
        current_user_id: ID аутентифицированного пользователя
        session: Асинхронная сессия базы данных
        redis: Асинхронное подключение к Redis для кеширования
        
    Returns:
        OrderOut: Pydantic модель с полной информацией о заказе:
            - id: UUID заказа
            - items: Список товаров
            - total_price: Общая стоимость
            - status: Текущий статус (PENDING, PAID, SHIPPED, CANCELED)
            - created_at: Время создания
        
    Raises:
        HTTPException 401: Пользователь не авторизован
        HTTPException 404: Заказ не найден или не принадлежит пользователю
        HTTPException 429: Превышен лимит запросов (10/минуту)
        
    Note:
        - Результат кешируется в Redis на 300 секунд (5 минут)
        - Ключ кеша формата: "order:{order_id}"
        - Кеш автоматически обновляется при изменении заказа
        - Пользователь имеет доступ только к своим заказам
    """
    # Формируем ключ для кеша
    cache_key = f"order:{order_id}"
    
    # Проверяем наличие заказа в кеше Redis
    cached_order = await redis.get(cache_key)
    if cached_order:
        return json.loads(cached_order)
    
    # Если в кеше нет, загружаем из базы данных
    order = await OrdersRepository.get_order_by_id(session, order_id, current_user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Преобразуем SQLAlchemy объект в Pydantic модель
    order_schema = OrderOut.model_validate(order)
    encoded = jsonable_encoder(order_schema)
    
    # Сохраняем в кеш на 300 секунд (5 минут)
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
    """Обновить статус заказа.
    
    Args:
        request: Объект запроса
        order_id: UUID заказа для обновления
        order_update: Новые данные заказа
        current_user_id: ID текущего пользователя
        session: Асинхронная сессия BD
        redis: Redis соединение для инвалидации кеша
        
    Returns:
        OrderOut: Обновленный объект заказа
        
    Raises:
        HTTPException: Заказ не найден
        
    Note:
        - Обновление кеша после обновления
    """
    db_order = await OrdersRepository.update_order(session, order_id, order_update, current_user_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    # обновим кеш новым данными заказа
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
@limiter.limit("10/minute")  # Ограничение: максимум 10 запросов в минуту
async def get_orders_user(
    request: Request,
    user_id: int = Depends(get_id_current_user),
    session: AsyncSession = Depends(get_async_session)
    ):
    """Получить все заказы текущего пользователя.
    
    Возвращает полный список всех заказов пользователя, упорядоченных
    по дате создания (от новых к старым). user_id автоматически
    извлекается из JWT токена, поэтому пользователь может видеть
    только свои заказы.
    
    Args:
        request: Объект HTTP запроса (для rate limiting)
        user_id: ID пользователя (автоматически из JWT токена)
        session: Асинхронная сессия базы данных
        
    Returns:
        OrdersResponse: Pydantic модель со списком заказов:
            {
                "orders": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "items": [{"laptop": 1}],
                        "total_price": 999.99,
                        "status": "PAID",
                        "created_at": "2024-02-09T10:30:00Z"
                    },
                    ...
                ]
            }
        
    Raises:
        HTTPException 401: Пользователь не авторизован
        HTTPException 404: Пользователь не существует
        HTTPException 429: Превышен лимит запросов (10/минуту)
        
    Note:
        - Возвращает пустой список, если у пользователя нет заказов
        - Заказы автоматически фильтруются по user_id
        - Результат не кешируется (список может часто меняться)
        - Можно добавить пагинацию для больших списков
    """
    # Получаем все заказы пользователя из базы данных
    orders = await OrdersRepository.get_orders_by_user_id(session, user_id)
    
    return {"orders": orders}