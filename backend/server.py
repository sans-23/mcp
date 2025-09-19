import asyncio
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Optional

from client import MCPClient
from api_models import ChatRequest, ChatResponse

from fastapi.middleware.cors import CORSMiddleware

# Global client instance
client: Optional[MCPClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = MCPClient()
    try:
        await client.connect_to_servers()
        await client.list_all_tools()
        yield
    except Exception as e:
        print(f"Startup failed: {e}")
        # Consider a more robust error handling strategy,
        # e.g., shutting down the app or logging the error and continuing.
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
    allow_origins=origins, # List of allowed origins
    allow_credentials=True, # Allow cookies, authorization headers, etc.
    allow_methods=["*"], # Allow all HTTP methods
    allow_headers=["*"], # Allow all headers
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=503, detail="Service is not ready. Please try again later.")
        
    try:
        chat_id, chat_session = await client.get_or_create_chat_session(request.chat_id)
        
        response_text = await client.process_query(chat_id, request.query)
        
        # Save the conversation to the JSON file
        await client._save_chat_history(chat_id, request.query, response_text)

        return ChatResponse(
            response=response_text,
            chat_id=chat_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)