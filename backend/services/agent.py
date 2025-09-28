from typing import List, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

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

async def initialize_global_agent(llm_instance: ChatOpenAI, tools_list: List[Any]) -> Optional[AgentExecutor]:
    executor = create_mcp_agent_executor(llm_instance, tools_list)
    return executor

async def get_agent_response(agent_executor: AgentExecutor, user_input: str, chat_history: List[BaseMessage]) -> Tuple[str, List[str]]:
    """Gets a response from the agent and returns the text and tools used."""
    agent_input = {"input": user_input, "chat_history": chat_history}
    response_parts = ""
    tool_names_used = []
    try:
        async for chunk in agent_executor.astream(agent_input):
            if "actions" in chunk:
                for action in chunk["actions"]:
                    tool_names_used.append(action.tool)
            
            if "output" in chunk:
                response_parts += chunk["output"]

    except Exception as e:
        print(f"💥 Agent Execution Error: {e}")
        response_parts = "I apologize, the AI agent encountered an error."
    
    unique_tool_names = sorted(list(set(tool_names_used)))

    return response_parts.strip(), unique_tool_names
