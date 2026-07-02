from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.database import get_db, Session
from utils.dependencies import get_current_user
from models.user import User
from models.workspace import Workspace
from models.workspace_integration import WorkspaceIntegrations
from utils.validators import is_dangerous, is_valid_email_format
from utils.notion_api_validator import is_valid_notion_credentials
from utils.jira_api_validator import is_valid_jira_credentials
from utils.encryption import encrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

router = APIRouter()

class NotionIntegrationRequest(BaseModel):
	api_key: str

class JiraIntegrationRequest(BaseModel):
    base_url: str
    admin_email: str
    api_key: str

# Notion Integration Endpoint

@router.patch("/workspaces/{workspace_id}/integrations/notion", status_code=200)
def	save_notion_integration(request: NotionIntegrationRequest, workspace_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	try:
		workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

		if workspace is None:
			raise HTTPException(status_code=404, detail="Workspace not found")
		
		if workspace.created_by != current_user.id:
			raise HTTPException(status_code=403, detail="Only the workspace owner can configure integrations")
		
		if is_dangerous(request.api_key):
			raise HTTPException(status_code=400, detail="Invalid Notion credentials, contains dangerous characters")
		
		if not is_valid_notion_credentials(request.api_key):
			raise HTTPException(status_code=400, detail="Invalid Notion credentials")
		
		encrypted_api_key = encrypt(request.api_key)

		if workspace.integration is None:
			workspace.integration = WorkspaceIntegrations(workspace = workspace)
			db.add(workspace.integration)
			db.flush()

		db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).update({"notion_api_key": encrypted_api_key, "notion_connected_at": func.now()})

		db.commit()
		db.refresh(workspace)
		db.refresh(workspace.integration)
		return {"message": "Notion credentials saved successfully"}

	except IntegrityError:
		db.rollback()
		raise HTTPException(status_code=409, detail="Integrity Error")
	

# Jira Integration Endpoint

@router.patch("/workspaces/{workspace_id}/integrations/jira", status_code=200)
def save_jira_integration(request: JiraIntegrationRequest, workspace_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        if workspace.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only the workspace owner can configure integrations")
        
        if is_dangerous(request.base_url) or is_dangerous(request.api_key) or is_dangerous(request.admin_email):
            raise HTTPException(status_code=400, detail="Invalid Jira credentials, contains dangerous characters")
        
        if not is_valid_email_format(request.admin_email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not is_valid_jira_credentials(request.base_url, request.admin_email, request.api_key):
            raise HTTPException(status_code=400, detail="Invalid Jira credentials")
        
        encrypted_api_key = encrypt(request.api_key)

        if workspace.integration is None:
            workspace.integration = WorkspaceIntegrations(workspace=workspace)
            db.add(workspace.integration)
            db.flush()

        db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).update({
            "jira_api_key": encrypted_api_key,
            "jira_base_url": request.base_url,
            "jira_admin_email": request.admin_email,
            "jira_connected_at": func.now()
        })

        db.commit()
        db.refresh(workspace)
        db.refresh(workspace.integration)
        return {"message": "Jira integration saved successfully"}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Integrity Error")