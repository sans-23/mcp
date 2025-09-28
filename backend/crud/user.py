from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(username=user.username)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
