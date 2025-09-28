from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient # type: ignore
from langchain.tools import Tool # type: ignore
from core import config
from services.rag import query_vector_database

async def _run_rag_query(query: str) -> str:
    """
    Runs a RAG query against the vector database and returns the results.
    """
    docs = await query_vector_database(query)
    if docs:
        return "\n\n".join([doc.page_content for doc in docs])
    return "No relevant information found in the knowledge base."

async def setup_tools() -> List[Any]:
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
        func=_run_rag_query,
        description="Useful for answering questions by retrieving information from a knowledge base. Input should be a clear and concise question."
    )
    
    return mcp_tools + [rag_tool]
