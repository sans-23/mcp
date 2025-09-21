import asyncio
from fastapi import FastAPI, HTTPException, Depends # type: ignore
from contextlib import asynccontextmanager
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.future import select # type: ignore

from client import MCPClient
from api_models import ChatRequest, ChatResponse, ChatHistoryResponse, MessageResponse
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from database import engine, Base, get_db_session
from models import ChatSession, ChatMessage

# Global client instance
client: Optional[MCPClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = MCPClient()
    try:
        # Create database tables on startup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await client.connect_to_servers()
        await client.list_all_tools()
        yield
    except Exception as e:
        print(f"Startup failed: {e}")
    finally:
        if client:
            await client.cleanup()

app = FastAPI(lifespan=lifespan)

# Define allowed origins for your front-end
origins = [
    "http://localhost:5173", # Your React app's development server
    "http://127.0.0.1:5173", # Another common local dev address
    # Add your production front-end URL here when deploying
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db_session)):
    if not client:
        raise HTTPException(status_code=503, detail="Service is not ready. Please try again later.")

    try:
        chat_id, chat_session = await client.get_or_create_chat_session(db, request.chat_id)
        response_text = await client.process_query(db, chat_id, request.query)
        
        return ChatResponse(
            response=response_text,
            chat_id=chat_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {e}")

@app.get("/chats", response_model=List[str])
async def get_all_chats(db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a list of all chat session IDs.
    """
    try:
        result = await db.execute(select(ChatSession.id).order_by(ChatSession.created_at.desc()))
        chat_ids = result.scalars().all()
        return chat_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chats: {e}")

@app.get("/chat/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_history(chat_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves the full history of a specific chat session.
    """
    try:
        # Check if chat session exists
        session_result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
        chat_session = session_result.scalars().first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        
        # Retrieve all messages for the session
        messages_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == chat_id)
            .order_by(ChatMessage.created_at)
        )
        messages = messages_result.scalars().all()

        return ChatHistoryResponse(
            chat_id=chat_id,
            messages=messages
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {e}")

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)