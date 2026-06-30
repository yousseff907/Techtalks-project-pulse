from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.integrations import router as integrations_router

from models.user import User
from models.verification import Verification
from models.email_rate_limit import EmailRateLimit
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_integration import WorkspaceIntegrations
from models.workspace_data import WorkspaceData
from utils.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(integrations_router)

