from fastapi import FastAPI
from contextlib import asynccontextmanager
from core import config
from db.base import Base
from db.session import engine
from api.v1.api import api_router
from services.llm import initialize_llm
from services.tools import setup_tools
from services.agent import initialize_global_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes LLM, tools, and the agent executor when the application starts."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    llm_instance = initialize_llm(
        config.OPENROUTER_API_KEY, 
        config.OPENROUTER_BASE_URL, 
        config.LLM_MODEL_NAME
    )
    tools_list = await setup_tools()
    if llm_instance:
        await initialize_global_agent(
            llm_instance, 
            tools_list
        )
    yield

app = FastAPI(
    title="Persistent LangChain MCP Agent API",
    description="A service for managing stateful chat sessions with a tool-using LangChain agent.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
