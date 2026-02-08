from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis.asyncio import Redis

from app.core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, REDIS_URL


DB_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


engine = create_async_engine(
    DB_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  
    echo=False  
    )


SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_async_session():
    async with SessionLocal() as session:
        yield session


async def get_redis():
    redis_app = await Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield redis_app
    finally:
        await redis_app.close()