"""Конфигурация приложения.

Этот модуль загружает переменные окружения из .env файла
и содержит все настройки для подключения к БД и кеш-сервисам.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Загружаем переменные из .env файла
load_dotenv()

# ========== POSTGRESQL КОНФИГУРАЦИЯ ==========
DB_HOST = os.environ.get('POSTGRES_HOST')
DB_PORT = os.environ.get('POSTGRES_PORT')
DB_NAME = os.environ.get('POSTGRES_DB')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

# ========== REDIS КОНФИГУРАЦИЯ ==========
# Основное Redis подключение для кеширования
REDIS_URL = os.environ.get('REDIS_URL')
# Redis для rate limiting
REDIS_URL_RATE_LIMIT = os.environ.get('REDIS_URL_RATE_LIMIT')
# Redis для Celery результатов
REDIS_URL_CELERY = os.environ.get('REDIS_URL_CELERY')

# ========== RABBITMQ КОНФИГУРАЦИЯ ==========
# URL подключения к RabbitMQ для message queue
RABBITMQ_URL = os.environ.get('RABBITMQ_URL')

# ========== ПУТИ ПРИЛОЖЕНИЯ ==========
BASE_DIR = Path(__file__).parent.parent.parent


class AuthJWT(BaseModel):
    """Конфигурация для JWT токенов.
    
    Attributes:
        private_key_path: Путь к приватному ключу для подписи токенов
        public_key_path: Путь к публичному ключу для проверки токенов
        algorithm: Алгоритм подписи (RS256 - RSA)
        expiration: Время истечения токена в минутах
    """
    private_key_path: Path = BASE_DIR / ".secret_key" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / ".secret_key" / "jwt-public.pem"
    algorithm: str = "RS256"  # RSA 256-bit
    expiration: int = 60  # 60 минут


auth = AuthJWT()