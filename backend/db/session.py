import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
from core.config import DATABASE_URL

# Create the asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session maker to manage sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency function to get an async database session
async def get_db_session():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
