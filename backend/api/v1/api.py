from fastapi import APIRouter # type: ignore
from api.v1.endpoints import users, sessions

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
