from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.integrations import router as integrations_router
from routes.workspaces import router as workspaces_router
from routes.users import router as users_router   #

from models.user import User  # noqa: F401
from models.verification import Verification  # noqa: F401
from models.email_rate_limit import EmailRateLimit  # noqa: F401
from models.workspace import Workspace  # noqa: F401
from models.workspace_member import WorkspaceMember  # noqa: F401
from models.workspace_integration import WorkspaceIntegrations  # noqa: F401
from models.workspace_data import WorkspaceData  # noqa: F401
from utils.database import Base, engine
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(integrations_router)
app.include_router(users_router)