from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from utils.validators import is_dangerous, is_blank
from utils.database import get_db, Session
from utils.dependencies import get_current_user

from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_integration import WorkspaceIntegrations

router = APIRouter()


class UpdateUsernameRequest(BaseModel):
    username: str


@router.get("/users/me", status_code=200)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }

@router.delete("/users/me", status_code=200)
def delete_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        owned_workspaces = db.query(Workspace).filter(Workspace.created_by == current_user.id).all()

        workspaces_to_transfer = []

        for workspace in owned_workspaces:
            member_count = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).count()

            if member_count <= 1:
                db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).delete()
                db.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace.id).delete()
                db.delete(workspace)
                continue

            next_admin = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.role == "admin"
            ).order_by(WorkspaceMember.joined_at.asc()).first()

            if not next_admin:
                raise HTTPException(
                    status_code=400,
                    detail="You own workspaces with no admin. Please promote a member to admin or delete the workspace before deleting your account"
                )

            workspaces_to_transfer.append((workspace, next_admin.user_id))

        for workspace, new_owner_id in workspaces_to_transfer:
            workspace.created_by = new_owner_id
            db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.user_id == new_owner_id
            ).update({"role": "owner"})

        db.query(User).filter(User.id == current_user.id).delete(synchronize_session=False)
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    return {"message": "Account deleted successfully"}


@router.patch("/users/me", status_code=200)
def update_username(
    request: UpdateUsernameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if is_dangerous(request.username):
        raise HTTPException(status_code=400, detail="Invalid username, contains dangerous characters")

    if is_blank(request.username):
        raise HTTPException(status_code=400, detail="Username cannot be blank")

    user = db.query(User).filter(User.id == current_user.id).first()
    user.username = request.username.strip()
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username}