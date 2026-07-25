from celery import Celery
from config import REDIS_URL
from celery.schedules import crontab

# Ensure all models are registered with SQLAlchemy's mapper registry
# before any task runs, since the worker process doesn't go through app.py
import models.workspace  # noqa: F401
import models.workspace_integration  # noqa: F401
import models.workspace_member  # noqa: F401
import models.workspace_data  # noqa: F401
import models.user  # noqa: F401
import models.verification  # noqa: F401
import models.email_rate_limit  # noqa: F401


celery_app = Celery("project-pulse", broker=REDIS_URL, backend=REDIS_URL, include=["services.sync.tasks"])

celery_app.conf.beat_schedule = {"sync across all workspaces" : {"task" : "services.sync.tasks.sync_all_active_workspaces",
																 "schedule" : crontab(minute="*/30")
																}
								}