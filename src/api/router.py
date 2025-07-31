from fastapi import APIRouter

from src.api.routes import private, utils
from src.apps.auth.urls import router as auth_router
from src.apps.demo.urls import router as demo_router
from src.apps.users.urls import router as users_router
from src.core.config import settings

api_router = APIRouter()

# Include auth routes (clean auth endpoints)
api_router.include_router(auth_router)

# Include user management routes (no auth endpoints)
api_router.include_router(users_router)

# Include utility routes
api_router.include_router(utils.router)

# Include DDD apps
api_router.include_router(demo_router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
