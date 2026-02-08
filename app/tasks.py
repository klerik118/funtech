import time
from app.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_order_task(self, order_id: str):
    try:
        time.sleep(2)
        print(f"Order {order_id} processed")
        return {f"Order {order_id} processed"} 
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
