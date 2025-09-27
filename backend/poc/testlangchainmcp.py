import os
import json
from typing import List, Dict, Any, Tuple
import asyncio
from pydantic import BaseModel, Field

# Using LangChain components for abstraction and robustness
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage

# --- 1. Configuration & Constants ---
# OpenRouter API Key and LLM Configuration
# NOTE: In a real-world scenario, use `os.environ.get('OPENROUTER_API_KEY')`
# to load this from an environment variable for security.
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

# --- 2. LLM Initialization (Robustness to Change) ---
def initialize_llm(api_key: str, base_url: str, model_name: str) -> ChatOpenAI:
    """Initializes and returns a ChatOpenAI instance compatible with OpenRouter."""
    try:
        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0,
            streaming=True
        )
        print("✅ LLM initialized successfully.")
        return llm
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        raise

# --- 3. Tool Setup (MCP and Future Tools) ---
async def setup_tools() -> List[Any]:
    """Sets up and returns a list of tools, including MCP-based ones."""
    try:
        client = MultiServerMCPClient(MCP_SERVERS)
        mcp_tools = await client.get_tools()
        print("✅ MCP tools fetched successfully.")
        
        tools = mcp_tools

        # Future Tools Placeholder: RAG and Database tools would be added here
        # Example:
        # from langchain_community.tools import Tool
        # tools.append(Tool(...))
        
        return tools
    except Exception as e:
        print(f"❌ Error setting up tools: {e}")
        raise

# --- 4. Agent and Chain Construction ---
def create_mcp_agent_executor(llm: ChatOpenAI, tools: List[Any]) -> AgentExecutor:
    """Creates and returns a robust agent executor with a prompt template."""
    # A prompt is essential for guiding the agent's behavior and tool usage.
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an AI assistant specialized in using external tools to answer questions. You have access to the following tools to fulfill user requests."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Use create_openai_tools_agent, as it's the correct way to build a tool-using agent
    # for OpenAI-compatible models and the latest LangChain agent framework.
    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    # An AgentExecutor is a runtime that uses the agent, tools, and input to reason and act.
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- 5. Chat History/Persistence (Future-ready) ---
class ChatManager:
    """Manages chat history, ready for future integration with databases."""
    def __init__(self):
        # A simple list of LangChain messages to maintain conversational context.
        self.history: List[Any] = []

    def get_history_messages(self) -> List[Any]:
        return self.history

    def add_message(self, message: Any):
        self.history.append(message)

# --- 6. Main Execution Loop ---
async def run_chat_client():
    """Main function to initialize and run the interactive chat client."""
    chat_manager = ChatManager()

    print("\n--- LangChain MCP Client Initialized ---")
    print("Agent is ready. Use 'exit' or 'quit' to end the session.")
    print("Try asking about a GitHub feature, e.g.: 'What is the syntax for a React functional component?'\n")

    try:
        # 1. Setup
        llm = initialize_llm(OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL_NAME)
        tools = await setup_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        agent_executor = create_mcp_agent_executor(llm, tools)
        
        # 2. Interactive Loop
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Session ended. Goodbye! 👋")
                break

            try:
                # 3. Prepare Input for the Agent
                # The agent expects 'input' (the current query) and 'chat_history' (for context)
                agent_input = {
                    "input": user_input,
                    "chat_history": chat_manager.get_history_messages()
                }

                # 4. Run the Agent and Stream the Response
                print("\nAI: ", end="", flush=True)

                # The `stream` method is more efficient and handles tokens one by one.
                response_parts = ""
                async for chunk in agent_executor.astream(agent_input):
                    # We are only interested in the final output message
                    if "output" in chunk:
                        response_part = chunk["output"]
                        print(response_part, end="", flush=True)
                        response_parts += response_part
                
                # 5. Update History
                if response_parts:
                    chat_manager.add_message(HumanMessage(content=user_input))
                    chat_manager.add_message(AIMessage(content=response_parts))
                
                print("\n") # Newline for next prompt
                
            except Exception as e:
                print(f"\n[ERROR] An error occurred during agent execution: {e}")
                print("\n")

    except Exception as e:
        print(f"\n[FATAL ERROR] Failed to initialize the client: {e}")
        
    finally:
        # Gracefully handle the end of the script
        print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(run_chat_client())