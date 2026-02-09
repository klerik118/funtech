"""Конфигурация Celery приложения для асинхронной обработки задач.

Викользует:
- RabbitMQ в качестве message broker
- Redis в качестве backend для хранения результатов
"""

from celery import Celery
from app.core.config import RABBITMQ_URL, REDIS_URL_CELERY, REDIS_URL

# Инициализация Celery с параметрами подключения
celery_app = Celery(    
    'order_service',
    broker=RABBITMQ_URL,
    backend=REDIS_URL_CELERY or REDIS_URL,
    include=['app.tasks']
)

# Конфигурация Celery: сериализация, таймауты, параллелизм
celery_app.conf.update(
    task_serializer='json',  # Сериализация задач в JSON
    accept_content=['json'],  # Принимаемый формат
    result_serializer='json',  # Сериализация результатов
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,  # Отслеживание начала выполнения задач
    task_time_limit=30 * 60,  # Таймаут выполнения задачи (30 минут)
    worker_prefetch_multiplier=1,  # Worker берёт по одной задаче за раз
)
