from celery_app import celery_app
from utils.database import SessionLocal
from models.workspace_integration import WorkspaceIntegrations
from sqlalchemy import func
from utils.redis_client import redis_client
from services.sync.jira_sync import gather_and_store_jira_users
from services.sync.notion_sync import gather_and_store_notion_users

@celery_app.task
def sync_workspace_data(workspace_id: int):
	db = SessionLocal()
	try:
		integration = db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).first()

		if not integration:
			return

		# Jira sync, uncomment once Nour's functions exist:
		if integration.jira_api_key:
			gather_and_store_jira_users(workspace_id, db)
			# gather_and_store_jira_projects(workspace_id, db)
			# gather_and_store_jira_tasks(workspace_id, db)
			pass

		# Notion sync, uncomment once Abbas's functions exist:
		if integration.notion_api_key:
			gather_and_store_notion_users(workspace_id, db)
			# gather_and_store_notion_databases(workspace_id, db)
			# gather_and_store_notion_tasks(workspace_id, db)
			pass
		
		redis_client.setex(f"sync_cooldown:{workspace_id}", 300, "1")
		db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).update({"last_synced_at": func.now()})
		db.commit()
	finally:
		db.close()


@celery_app.task
def sync_all_active_workspaces():
	db = SessionLocal()
	try:
		integrations = db.query(WorkspaceIntegrations).all()
		for integration in integrations:
			cooldown_key = f"sync_cooldown:{integration.workspace_id}"
			if redis_client.exists(cooldown_key):
				continue
			sync_workspace_data.delay(integration.workspace_id)
	finally:
		db.close()