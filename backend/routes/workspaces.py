from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.database import get_db, Session
from utils.dependencies import get_current_user
from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_integration import WorkspaceIntegrations
from utils.validators import is_dangerous
from sqlalchemy.exc import IntegrityError
import secrets
from config import APP_BASE_URL

router = APIRouter()

class CreateWorkspaceRequest(BaseModel):
	name: str

@router.post("/workspaces", status_code=201)
def	create_workspace(request: CreateWorkspaceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	max_workspaces = 5

	if is_dangerous(request.name):
		raise HTTPException(status_code=400, detail="Invalid name, contains dangerous characters")
	
	workspace_count = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).count()
	if workspace_count >= max_workspaces:
		raise HTTPException(status_code=400, detail=f"You have reached the maximum number of workspaces ({max_workspaces})")

	workspace_count = db.query(Workspace).count()

	for _ in range (0, workspace_count):
		try:
			invitation_code = secrets.token_urlsafe(16)
			new_workspace = Workspace(name=request.name, created_by=current_user.id, invite_code=invitation_code, invite_link=APP_BASE_URL+'/'+str(invitation_code))
			db.add(new_workspace)
			db.flush()
			new_workspace.integration = WorkspaceIntegrations(workspace_id=new_workspace.id, workspace=new_workspace)
			new_member = WorkspaceMember(user_id=current_user.id, workspace_id=new_workspace.id, role="owner")
			db.add(new_member)
			db.add(new_workspace.integration)
			db.commit()
			db.refresh(new_workspace)
			db.refresh(new_member)
			db.refresh(new_workspace.integration)
			return {"workspace_id": new_workspace.id, "name": new_workspace.name, "invite_code": new_workspace.invite_code, "invite_link": new_workspace.invite_link}
		except IntegrityError:
			db.rollback()
