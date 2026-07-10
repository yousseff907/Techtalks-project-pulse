from celery import Celery
from config import REDIS_URL
from celery.schedules import crontab

celery_app = Celery("project-pulse", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {"sync across all workspaces" : {"task" : "services.sync.tasks.sync_all_active_workspaces",
																 "schedule" : crontab(minute="*/30")
																}
								}