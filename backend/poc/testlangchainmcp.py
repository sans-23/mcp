import os
import asyncio
from typing import List, Dict, Any, Optional

# FastAPI and Pydantic for API structure
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# LangChain components
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, message_to_dict

# --- 1. Configuration & Constants ---

# NOTE: In a real-world scenario, use environment variables.
# We use the provided values for demonstration purposes.
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL_NAME = "x-ai/grok-4-fast:free"

# MCP Server Configuration
MCP_SERVERS = {
    "github": {
        "transport": "streamable_http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            "Authorization": "Bearer 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"
        }
    }
}

# --- 2. Global State & Initialization Functions ---

# Global variables to hold the initialized components
agent_executor: Optional[AgentExecutor] = None
llm: Optional[ChatOpenAI] = None
tools: List[Any] = []

def initialize_llm(api_key: str, base_url: str, model_name: str) -> ChatOpenAI:
    """Initializes and returns a ChatOpenAI instance compatible with OpenRouter."""
    try:
        # Note: Streaming is set to False here because we are collecting the 
        # full response before sending it back in the non-streaming API endpoint.
        llm_instance = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0,
            streaming=False # Set to False for non-streaming API response
        )
        print("✅ LLM initialized successfully.")
        return llm_instance
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        # In a real app, this should crash the startup to prevent a broken service
        raise

async def setup_tools() -> List[Any]:
    """Sets up and returns a list of tools, including MCP-based ones."""
    try:
        client = MultiServerMCPClient(MCP_SERVERS)
        mcp_tools = await client.get_tools()
        print(f"✅ MCP tools fetched successfully. Found {len(mcp_tools)} tools.")
        return mcp_tools
    except Exception as e:
        print(f"❌ Error setting up tools: {e}")
        raise

def create_mcp_agent_executor(llm_instance: ChatOpenAI, tools_list: List[Any]) -> AgentExecutor:
    """Creates and returns a robust agent executor with a prompt template."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an AI assistant specialized in using external tools to answer questions. You have access to the following tools to fulfill user requests."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(
        llm=llm_instance,
        tools=tools_list,
        prompt=prompt
    )

    executor = AgentExecutor(agent=agent, tools=tools_list, verbose=True)
    print("✅ Agent Executor created successfully.")
    return executor

# --- 3. Pydantic Models for API ---

class Message(BaseModel):
    """Represents a single message in the chat history."""
    type: str = Field(..., description="The type of message, e.g., 'human' or 'ai'.")
    content: str = Field(..., description="The text content of the message.")

class ChatRequest(BaseModel):
    """The input structure for the chat endpoint."""
    input: str = Field(..., description="The user's current query.")
    # Chat history is passed in to maintain statelessness in the API design.
    chat_history: List[Message] = Field(default=[], description="The previous conversation messages.")

class ChatResponse(BaseModel):
    """The output structure for the chat endpoint."""
    response: str = Field(..., description="The agent's final response.")
    tool_names_used: List[str] = Field(default=[], description="List of tools utilized by the agent.")

# --- 4. FastAPI Application Setup ---

app = FastAPI(
    title="LangChain MCP Agent FastAPI",
    description="A service exposing a tool-using LangChain agent powered by Multi-Server Copilot (MCP) via OpenRouter.",
    version="1.0.0"
)

# Startup event to initialize the heavy components once
@app.on_event("startup")
async def startup_event():
    """Initializes LLM, tools, and the agent executor when the application starts."""
    global llm, tools, agent_executor
    try:
        llm = initialize_llm(OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL_NAME)
        tools = await setup_tools()
        agent_executor = create_mcp_agent_executor(llm, tools)
    except Exception as e:
        print(f"🛑 FATAL: Startup failed due to error: {e}")
        # Raising the exception will prevent the server from starting
        raise

# --- 5. API Endpoints ---

def _convert_pydantic_history_to_lc_messages(history: List[Message]) -> List[BaseMessage]:
    """Converts the Pydantic message list from the request body to LangChain's BaseMessage list."""
    lc_messages = []
    for msg in history:
        if msg.type.lower() == "human":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.type.lower() == "ai":
            lc_messages.append(AIMessage(content=msg.content))
        # Ignore other types for simplicity or raise an error for invalid types
    return lc_messages


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Handles a user query, runs the agent, and returns the response.
    """
    if agent_executor is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized. Server is starting up.")

    try:
        # Convert incoming Pydantic history models into LangChain BaseMessage objects
        lc_chat_history = _convert_pydantic_history_to_lc_messages(request.chat_history)

        # Prepare the input dictionary for the agent executor
        agent_input = {
            "input": request.input,
            "chat_history": lc_chat_history
        }

        # Run the agent synchronously within the async context
        # We use astream and collect output for full response in one API call
        response_parts = ""
        # The .astream() method yields objects that contain the steps and the final output.
        # We collect the final output part.
        async for chunk in agent_executor.astream(agent_input):
            if "output" in chunk:
                response_parts += chunk["output"]

        # Note: Extracting used tool names is complex with the latest agent stream, 
        # as the tools are typically logged in the 'intermediate_steps' which are 
        # mixed with the final output. For this migration, we will keep the 
        # tool_names_used list empty or you'd need more complex parsing of the chunks.
        # Let's keep it simple and just return the final response text.
        
        return ChatResponse(
            response=response_parts.strip(),
            tool_names_used=[] # Placeholder for simplicity
        )

    except Exception as e:
        # Log the error for debugging
        print(f"💥 Agent Execution Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during chat execution: {e}")


# --- 6. Execution Block ---

if __name__ == "__main__":
    # Command to run the server: uvicorn fastapi_mcp_chat:app --reload
    # This block allows running the file directly for testing.
    print("\n--- Starting FastAPI Server ---")
    print("Access the API docs at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)