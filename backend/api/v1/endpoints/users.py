from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserCreate, UserSchema
from crud import user as user_crud
from db.session import get_db_session

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    """Creates a new user in the database."""
    db_user = await user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await user_crud.create_user(db=db, user=user)
