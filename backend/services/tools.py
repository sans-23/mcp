from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient # type: ignore
from langchain.tools import Tool # type: ignore
from core import config
from services.rag import query_vector_database

async def _run_rag_query(query: str, llm: Any) -> str:
    """
    Runs a RAG query against the vector database and returns the results.
    """
    docs, _ = await query_vector_database(query, llm)
    if docs:
        return docs
    return "No relevant information found in the knowledge base."

async def setup_tools(llm: Any) -> List[Any]:
    """Sets up and returns a list of tools, including MCP-based ones and RAG tool."""
    mcp_tools = []
    try:
        if not all(server.get('headers') and server['headers'].get('Authorization') for server in config.MCP_SERVERS.values()):
            print("❌ WARNING: MCP Authorization headers missing. Skipping MCP tool setup.")
        else:
            client = MultiServerMCPClient(config.MCP_SERVERS)
            mcp_tools = await client.get_tools()
            print(f"✅ MCP tools fetched successfully. Found {len(mcp_tools)} tools.")
    except Exception as e:
        print(f"❌ Error setting up MCP tools: {e}")

    rag_tool = Tool(
        name="RAG_System",
        func=lambda query: _run_rag_query(query, llm),
        description="Doc for monopoly rules. Use this to answer questions about the rules of Monopoly.",
    )

    return mcp_tools + [rag_tool]
