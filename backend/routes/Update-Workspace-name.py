from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.database import get_db, Session
from utils.dependencies import get_current_user
from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from utils.validators import is_dangerous

router = APIRouter()

class UpdateWorkspaceNameRequest(BaseModel):
	name: str

@router.patch("/workspaces/{workspace_id}", status_code=200)
def	update_workspace_name(request: UpdateWorkspaceNameRequest, workspace_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
	if not workspace:
		raise HTTPException(status_code=404, detail="Workspace not found")

	membership = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id).first()
	if not membership:
		raise HTTPException(status_code=404, detail="You are not a member of this workspace")

	if membership.role != "owner" and membership.role != "admin":
		raise HTTPException(status_code=403, detail="Only the workspace owner or an admin can configure workspace settings")

	if is_dangerous(request.name):
		raise HTTPException(status_code=400, detail="Invalid name, contains dangerous characters")

	workspace.name = request.name.strip()
	db.commit()
	db.refresh(workspace)

	return {"workspace_id": workspace.id, "name": workspace.name}