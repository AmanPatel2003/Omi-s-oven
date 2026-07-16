from celery import Celery
from app.config import settings

celery_app = Celery(
    "cake_shop",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.order_tasks",
        "app.tasks.reminder_tasks",
        "app.tasks.inventory_tasks",
        "app.tasks.salary_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="Asia/Kolkata",
    beat_schedule={
        # Check low stock every day at 8 AM
        "check-low-stock": {
            "task": "app.tasks.inventory_tasks.check_low_stock_alert",
            "schedule": 86400,
        },
        # Send occasion reminders every day at 10 AM
        "send-occasion-reminders": {
            "task": "app.tasks.reminder_tasks.send_occasion_reminders",
            "schedule": 86400,
        },
    },
)
