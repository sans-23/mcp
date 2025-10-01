from typing import List, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from schemas.chat import LLMOutputBlock
import logging

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
    executor = executor.with_config({"run_name": "Jarvis"})
    print("✅ Agent Executor created successfully.")
    return executor

async def get_agent_response(agent_executor: AgentExecutor, user_input: str, chat_history: List[BaseMessage], llm_instance: ChatOpenAI) -> Tuple[LLMOutputBlock, List[str]]:
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
        response_parts = f"I apologize, the AI agent encountered an error. {e}"
    
    structured_llm = llm_instance.with_structured_output(LLMOutputBlock)
    pro = "You are an AI assistant. " \
    "Your responses should be structured as an array of content blocks, which can be either plain text or React components. " \
    "When presenting data analysis, statistics, or any information that can be visually represented, automatically generate a React component to render a suitable chart or graph (e.g., histogram, bar chart, line chart). " \
    "For React components, ensure the `code` field of the `ReactBlock` contains a string representing a default export of a React functional component. For example: '''export default function MyComponent() { return <div>Hello</div>; }'''. " \
    "Always provide some introductory and concluding text around any React components to make the conversation flow naturally. " \
    "Also, it should be compatible with this theme :root {font-family: system-ui, Avenir, Helvetica, Arial, sans-serif; line-height: 1.5; font-weight: 400; color-scheme: light dark; color: rgba(255, 255, 255, 0.87); background-color: #242424; font-synthesis: none; }"
    
    structured_response = await structured_llm.ainvoke(pro + response_parts)
    unique_tool_names = list(set(tool_names_used))

    return structured_response, unique_tool_names