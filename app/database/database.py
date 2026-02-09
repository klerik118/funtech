"""Конфигурация подключения к базам данных.

Этот модуль содержит:
- Настройку асинхронного подключения к PostgreSQL
- Кеширование с использованием Redis
- Создание сессий с использованием SQLAlchemy
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis.asyncio import Redis

from app.core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, REDIS_URL


# Формируем URL подключения к PostgreSQL с использованием asyncpg дривера
DB_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


# Создаем асинхронный движок с оптимизированными параметрами
engine = create_async_engine(
    DB_URL,
    pool_size=20,  # Размер пула соединений
    max_overflow=0,  # Максимально допустимое превышение размера пула
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False  # Логирование SQL запросов (False для продакшена)
    )


# Фабрика для создания асинхронных сессий
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_async_session():
    """Получить асинхронную сессию БД для использования в FastAPI зависимостях.
        AsyncSession: Асинхронная сессия для работы с БД
    """
    async with SessionLocal() as session:
        yield session


async def get_redis():
    """Получить асинхронное подключение к Redis для кеширования.
        Redis: Асинхронное подключение к Redis
    """
    redis_app = await Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield redis_app
    finally:
        await redis_app.close()