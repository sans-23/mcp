from fastapi import FastAPI
from contextlib import asynccontextmanager
from core import config
import services.services as services
from db.base import Base
from db.session import engine
from api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes LLM, tools, and the agent executor when the application starts."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    services.llm = services.initialize_llm(
        config.OPENROUTER_API_KEY, 
        config.OPENROUTER_BASE_URL, 
        config.LLM_MODEL_NAME
    )
    services.tools = await services.setup_tools()
    if services.llm:
        services.agent_executor = services.create_mcp_agent_executor(
            services.llm, 
            services.tools
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
