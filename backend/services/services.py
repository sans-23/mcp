from typing import List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from models.chat import ChatMessage
from core import config

agent_executor: Optional[AgentExecutor] = None
llm: Optional[ChatOpenAI] = None
tools: List[Any] = []

def initialize_llm(api_key: str, base_url: str, model_name: str) -> Optional[ChatOpenAI]:
    """Initializes and returns a ChatOpenAI instance."""
    if not api_key or not base_url:
        print("❌ WARNING: OPENROUTER_API_KEY or OPENROUTER_BASE_URL not set.")
        return None
    try:
        llm_instance = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0,
            streaming=False
        )
        print("✅ LLM initialized successfully.")
        return llm_instance
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        return None

async def setup_tools() -> List[Any]:
    """Sets up and returns a list of tools, including MCP-based ones."""
    try:
        if not all(server.get('headers') and server['headers'].get('Authorization') for server in config.MCP_SERVERS.values()):
            print("❌ WARNING: MCP Authorization headers missing. Skipping tool setup.")
            return []

        client = MultiServerMCPClient(config.MCP_SERVERS)
        mcp_tools = await client.get_tools()
        print(f"✅ MCP tools fetched successfully. Found {len(mcp_tools)} tools.")
        return mcp_tools
    except Exception as e:
        print(f"❌ Error setting up tools: {e}")
        return []

def create_mcp_agent_executor(llm_instance: ChatOpenAI, tools_list: List[Any]) -> Optional[AgentExecutor]:
    """Creates and returns an agent executor."""
    if not llm_instance:
        return None
        
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an AI assistant. Maintain conversation context using the provided chat history."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(llm=llm_instance, tools=tools_list, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools_list, verbose=True)
    print("✅ Agent Executor created successfully.")
    return executor

def db_messages_to_lc_messages(history_records: List[ChatMessage]) -> List[BaseMessage]:
    """Converts a list of ChatMessage DB objects to LangChain's BaseMessage list."""
    lc_messages = []
    for rec in history_records:
        if not rec.content or "text" not in rec.content:
            continue
            
        content_text = rec.content["text"]
        if rec.role.lower() == "user":
            lc_messages.append(HumanMessage(content=content_text))
        elif rec.role.lower() == "ai":
            lc_messages.append(AIMessage(content=content_text))
    return lc_messages

async def get_agent_response(agent_executor: AgentExecutor, user_input: str, chat_history: List[BaseMessage]) -> tuple[str, List[str]]:
    """Gets a response from the agent and returns the text and tools used."""
    agent_input = {"input": user_input, "chat_history": chat_history}
    response_parts = ""
    tool_names_used = []
    try:
        async for chunk in agent_executor.astream(agent_input):
            # The 'actions' key contains tool calls
            if "actions" in chunk:
                for action in chunk["actions"]:
                    tool_names_used.append(action.tool)
            
            if "output" in chunk:
                response_parts += chunk["output"]

    except Exception as e:
        print(f"💥 Agent Execution Error: {e}")
        response_parts = "I apologize, the AI agent encountered an error."
    
    # Remove duplicates
    unique_tool_names = sorted(list(set(tool_names_used)))

    return response_parts.strip(), unique_tool_names
