"""Асинхронные Celery задачи для обработки заказов.

Этот модуль содержит фоновые задачи, которые выполняются worker'ами Celery.
"""

import time
from app.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_order_task(self, order_id: str):
    """Обработка заказа в фоне.
    
    Задача выполняет обработку заказа асинхронно с повторными попытками
    при ошибках.
    
    Args:
        self: Контекст Celery задачи
        order_id: Уникальный идентификатор заказа
        
    Returns:
        dict: Словарь с результатом обработки
        
    Raises:
        Exception: При ошибке переотправляет задачу с задержкой в 60 секунд
        
    Note:
        - Максимум 3 повторных попытки при ошибке
        - Задержка перед повтором: 60 секунд
    """
    try:
        time.sleep(2)  # Имитация обработки
        print(f"Order {order_id} processed")
        return {f"Order {order_id} processed"} 
    except Exception as exc:
        # Переотправляем задачу с экспоненциальным увеличением задержки
        raise self.retry(exc=exc, countdown=60)
