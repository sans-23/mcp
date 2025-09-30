from fastapi import FastAPI # type: ignore
from contextlib import asynccontextmanager
from core import config
from db.base import Base
from db.session import engine
from api.v1.api import api_router
from services.llm import initialize_llm
from services.tools import setup_tools
from services.agent import initialize_global_agent
from services.rag import populate_vector_database
import os
from fastapi.middleware.cors import CORSMiddleware # type: ignore

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes LLM, tools, and the agent executor when the application starts."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        llm_instance = initialize_llm(
            config.OPENROUTER_API_KEY, 
            config.OPENROUTER_BASE_URL, 
            config.LLM_MODEL_NAME
        )
    except ValueError as e:
        print(f"❌ Error initializing LLM: {e}")
        llm_instance = None

    tools_list = await setup_tools(llm_instance)

    # Initialize RAG database
    pdf_path = "rag/data/monopoly.pdf"  # Adjust path as necessary
    if os.path.exists(pdf_path):
        await populate_vector_database(pdf_path)
    else:
        print(f"Warning: PDF file not found at {pdf_path}. RAG database will not be populated.")

    print(llm_instance)

    if llm_instance:
        app.state.llm_instance = llm_instance  # Store the LLM instance in the app state
        app.state.agent_executor = await initialize_global_agent(
            llm_instance, 
            tools_list
        )
        if app.state.agent_executor is None:
            print("❌ Agent Executor was not created.")
    else:
        print("❌ Agent not initialized due to LLM initialization failure.")
    yield

app = FastAPI(
    title="Persistent LangChain MCP Agent API",
    description="A service for managing stateful chat sessions with a tool-using LangChain agent.",
    version="1.0.0",
    lifespan=lifespan
)

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

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
