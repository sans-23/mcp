import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # type: ignore
from sqlalchemy.orm import declarative_base # type: ignore
from dotenv import load_dotenv # type: ignore

# Load the database URL from environment variables
# For local development, you might have this in a .env file.
# e.g., DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

# Create the asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session maker to manage sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for our ORM models
Base = declarative_base()

# Dependency function to get an async database session
async def get_db_session():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()