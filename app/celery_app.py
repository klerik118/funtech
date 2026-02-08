from celery import Celery
from app.core.config import RABBITMQ_URL, REDIS_URL_CELERY, REDIS_URL

celery_app = Celery(    
    'order_service',
    broker=RABBITMQ_URL,
    backend=REDIS_URL_CELERY or REDIS_URL,
    include=['app.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  
    worker_prefetch_multiplier=1,
)
