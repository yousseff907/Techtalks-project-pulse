from fastapi import APIRouter, HTTPException, Depends, Response, status
from pydantic import BaseModel
from utils.database import get_db, Session
from utils.dependencies import get_current_user
from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_integration import WorkspaceIntegrations
from models.workspace_data import WorkspaceData
from utils.validators import is_dangerous, is_blank
from sqlalchemy.exc import IntegrityError
import secrets
from config import APP_BASE_URL
from services.sync.tasks import sync_workspace_data
from utils.redis_client import redis_client
from sqlalchemy import and_, func, or_
from typing import Literal

router = APIRouter()

class CreateWorkspaceRequest(BaseModel):
	name: str

class JoinWorkspaceRequest(BaseModel):
    invite_code: str

class UpdateWorkspaceNameRequest(BaseModel):
	name: str

class UpdateMemberRoleRequest(BaseModel):
	role: Literal["admin", "member"]

@router.post("/workspaces", status_code=201)
def	create_workspace(request: CreateWorkspaceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	max_workspaces = 5

	if is_dangerous(request.name):
		raise HTTPException(status_code=400, detail="Invalid name, contains dangerous characters")
	
	if is_blank(request.name):
		raise HTTPException(status_code=400, detail="Name cannot be blank")

	workspace_count = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).count()
	if workspace_count >= max_workspaces:
		raise HTTPException(status_code=400, detail=f"You have reached the maximum number of workspaces ({max_workspaces})")

	workspace_count = db.query(Workspace).count()
	
	for _ in range (0, workspace_count + 1):
		try:
			invitation_code = secrets.token_urlsafe(16)
			new_workspace = Workspace(name=request.name.strip(), created_by=current_user.id, invite_code=invitation_code, invite_link=APP_BASE_URL+'/'+str(invitation_code))
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

@router.get("/workspaces")
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Workspace.id, Workspace.name, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == current_user.id)
        .all()
    )

    if not rows:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return [
        {"id": row.id, "name": row.name, "role": row.role}
        for row in rows
    ]

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
            total_members = (
                db.query(WorkspaceMember)
                .filter(WorkspaceMember.workspace_id == workspace_id)
                .count()
            )
            if total_members <= 1:
                db.delete(workspace)
                db.commit()
                return {"message": "Workspace deleted successfully as you were the only member"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Please promote a member to admin or delete the workspace before leaving",
                )
        
        workspace.created_by = next_admin.user_id
        next_admin.role = "owner"

    db.delete(membership)
    db.commit()
    
    return {"message": "Successfully left the workspace"}

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
      
	if is_blank(request.name):
		raise HTTPException(status_code=400, detail="Name cannot be blank")
      
	workspace.name = request.name.strip()
	db.commit()
	db.refresh(workspace)

	return {"workspace_id": workspace.id, "name": workspace.name}

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


@router.patch("/workspaces/{workspace_id}/invite-code", status_code=200)
def rotate_workspace_invite_code(
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

    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only workspace owners or admins can rotate the invite code",
        )

    workspace_count = db.query(Workspace).count()

    for _ in range(0, workspace_count + 1):
        new_code = secrets.token_urlsafe(16)
        workspace.invite_code = new_code
        workspace.invite_link = APP_BASE_URL + "/" + new_code

        try:
            db.commit()
            db.refresh(workspace)
            return {
                "workspace_id": workspace.id,
                "invite_code": workspace.invite_code,
                "invite_link": workspace.invite_link,
            }
        except IntegrityError:
            db.rollback()

    raise HTTPException(
        status_code=500,
        detail="Failed to generate a unique invite code",
    )

@router.get("/workspaces/{workspace_id}", status_code=200)
def	get_workspace_details(workspace_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
	if not workspace:
		raise HTTPException(status_code=404, detail="Workspace not found")

	membership = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id).first())
	if not membership:
		raise HTTPException(status_code=403, detail="You are not a member of this workspace")

	created_by = db.query(User).filter(User.id == workspace.created_by).first()

	member_count = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).count()

	return {"id" : workspace_id,
			"name" : workspace.name,
			"invite_code" : workspace.invite_code,
			"invite_link" : workspace.invite_link,
			"created_by" : created_by.username if created_by else "Deleted User",
			"created_at" : workspace.created_at,
			"member_count" : member_count}

@router.get("/workspaces/{workspace_id}/sync/status", status_code=200)
def get_sync_status(workspace_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
	if not workspace:
		raise HTTPException(status_code=404, detail="Workspace not found")
	
	membership = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id, WorkspaceMember.workspace_id == workspace_id).first()
	if not membership:
		raise HTTPException(status_code=403, detail="You are not a member of this workspace")

	integration = db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).first()
	if not integration:
		raise HTTPException(status_code=404, detail="Workspace not found")

	return {"last_synced_at": integration.last_synced_at}

@router.post("/workspaces/{workspace_id}/sync", status_code=202)
def	workspace_manual_sync(workspace_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
	if not workspace:
		raise HTTPException(status_code=404, detail="Workspace not found")

	membership = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id, WorkspaceMember.workspace_id == workspace_id).first()
	if not membership:
		raise HTTPException(status_code=403, detail="You are not a member of this workspace")

	if membership.role not in ["owner", "admin"]:
		raise HTTPException(status_code=403, detail="Only workspace owners or admins can trigger a manual sync")

	integration = db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).first()
	if not integration:
		raise HTTPException(status_code=404, detail="Workspace not found")

	cooldown_key = f"sync_cooldown:{workspace_id}"
	if redis_client.exists(cooldown_key):
		raise HTTPException(status_code=429, detail="A sync was recently triggered, please wait before trying again")

	task = sync_workspace_data.delay(workspace_id)
	redis_client.setex(cooldown_key, 300, "1")

	return {"task_id": task.id, "status": "queued"}


@router.get("/workspaces/{workspace_id}/members", status_code=200)
def list_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )
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
            status_code=403,
            detail="You are not a member of this workspace",
        )

    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == workspace_id)
        .first()
    )

    members = (
        db.query(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .filter(WorkspaceMember.workspace_id == workspace_id)
        .all()
    )

    workspace_users = []

    if integration:
        latest_jira = (
            db.query(func.max(WorkspaceData.fetched_at))
            .filter(
                WorkspaceData.integration_id == integration.workspace_id,
                WorkspaceData.type == "user",
                WorkspaceData.source == "jira",
            )
            .scalar()
        )

        latest_notion = (
            db.query(func.max(WorkspaceData.fetched_at))
            .filter(
                WorkspaceData.integration_id == integration.workspace_id,
                WorkspaceData.type == "user",
                WorkspaceData.source == "notion",
            )
            .scalar()
        )

        filters = []

        if latest_jira:
            filters.append(
                and_(
                    WorkspaceData.source == "jira",
                    WorkspaceData.fetched_at == latest_jira,
                )
            )

        if latest_notion:
            filters.append(
                and_(
                    WorkspaceData.source == "notion",
                    WorkspaceData.fetched_at == latest_notion,
                )
            )

        if filters:
            workspace_users = (
                db.query(WorkspaceData)
                .filter(
                    WorkspaceData.integration_id == integration.workspace_id,
                    WorkspaceData.type == "user",
                    or_(*filters),
                )
                .all()
            )
    def normalize(value):
        if not value:
            return None
        return str(value).strip().lower()

    jira_email = {}
    jira_name = {}

    notion_email = {}
    notion_name = {}

    for row in workspace_users:
        payload = row.payload or {}

        email = normalize(payload.get("email"))
        name = normalize(payload.get("name"))

        if row.source == "jira":
            if email:
                jira_email[email] = payload
            if name:
                jira_name[name] = payload

        elif row.source == "notion":
            if email:
                notion_email[email] = payload
            if name:
                notion_name[name] = payload

    def provider_result(match):
        if not match:
            return None

        return {
            "id": match.get("id"),
            "name": match.get("name"),
            "email": match.get("email"),
        }

    results = []

    for member, user in members:
        email = normalize(user.email)
        username = normalize(user.username)

        jira_match = (
            jira_email.get(email)
            or jira_name.get(username)
        )

        notion_match = (
            notion_email.get(email)
            or notion_name.get(username)
        )

        results.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": member.role,
                "jira": provider_result(jira_match),
                "notion": provider_result(notion_match),
            }
        )

    return results


@router.patch("/workspaces/{workspace_id}/members/{user_id}")
def	promote_demote_user(request: UpdateMemberRoleRequest, workspace_id: int, user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	workspace = (db.query(Workspace).filter(Workspace.id == workspace_id).first())
	if not workspace:
		raise HTTPException(status_code=404, detail="Workspace not found")

	membership = (db.query(WorkspaceMember).filter(	WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id).first())
	if not membership:
		raise HTTPException(status_code=403, detail="You are not a member of this workspace")

	if membership.role not in ["owner", "admin"]:
		raise HTTPException(status_code=403, detail="Only workspace owners or admins can change membership status")

	membership = (db.query(WorkspaceMember).filter(	WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).first())
	if not membership:
		raise HTTPException(status_code=404, detail="Target user is not a member of this workspace")

	if membership.role == "owner":
		raise HTTPException(status_code=400, detail="ownership must be transferred first via Leave Workspace or a separate transfer mechanism, this endpoint does not handle ownership transfer")

	membership.role = request.role
	db.commit()
	db.refresh(membership)
	
	return {"user_id": user_id, "workspace_id" : workspace_id, "role" : membership.role}

#Remove member from workspace

@router.delete("/workspaces/{workspace_id}/members/{user_id}", status_code=200)
def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    caller_membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )

    if not caller_membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this workspace",
        )

    if caller_membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only workspace owners or admins can remove members",
        )

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Use the Leave Workspace endpoint to remove yourself",
        )

    target_membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )

    if not target_membership:
        raise HTTPException(
            status_code=404,
            detail="Target user is not a member of this workspace",
        )

    if target_membership.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Workspace owner cannot be removed",
        )

    db.delete(target_membership)
    db.commit()

    return {"message": "Member removed successfully"}