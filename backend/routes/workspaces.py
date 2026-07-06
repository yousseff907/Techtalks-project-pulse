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

class JoinWorkspaceRequest(BaseModel):
    invite_code: str

@router.post("/workspaces", status_code=201)
def	create_workspace(request: CreateWorkspaceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	max_workspaces = 5

	if is_dangerous(request.name):
		raise HTTPException(status_code=400, detail="Invalid name, contains dangerous characters")
	
	workspace_count = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).count()
	if workspace_count >= max_workspaces:
		raise HTTPException(status_code=400, detail=f"You have reached the maximum number of workspaces ({max_workspaces})")

	workspace_count = db.query(Workspace).count()

	for _ in range (0, workspace_count + 1):
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

@router.post("/workspaces/join")
def join_workspace(
    body: JoinWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if is_dangerous(body.invite_code):
        raise HTTPException(
            status_code=400,
            detail="Invalid invite code",
        )

    workspace = (
        db.query(Workspace)
        .filter(Workspace.invite_code == body.invite_code)
        .first()
    )
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Invalid invite code",
        )

    existing_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.workspace_id == workspace.id,
        )
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="You are already a member of this workspace",
        )

    workspace_count = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == current_user.id)
        .count()
    )
    if workspace_count >= 5:
        raise HTTPException(
            status_code=400,
            detail="You have reached the maximum number of workspaces (5)",
        )

    new_member = WorkspaceMember(
        user_id=current_user.id,
        workspace_id=workspace.id,
        role="member",
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return {
        "workspace_id": workspace.id,
        "name": workspace.name,
    }


@router.delete("/workspaces/{workspace_id}/leave", status_code=200)
def leave_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=404,
            detail="You are not a member of this workspace",
        )

    if membership.role == "owner":
        next_admin = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "admin",
            )
            .order_by(WorkspaceMember.joined_at.asc())
            .first()
        )
        if not next_admin:
            raise HTTPException(
                status_code=400,
                detail="You own workspaces with no admin. Please promote a member to admin or delete the workspace before leaving",
            )
        
        workspace.created_by = next_admin.user_id
        next_admin.role = "owner"

    db.delete(membership)
    db.commit()
    
    return {"message": "Successfully left the workspace"}


#Delete workspace

@router.delete("/workspaces/{workspace_id}", status_code=200)
def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )

    if not membership or membership.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the workspace owner can delete this workspace",
        )

    db.delete(workspace)
    db.commit()

    return {"message": "Workspace deleted successfully"}