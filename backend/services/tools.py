from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient # type: ignore
from langchain.tools import Tool # type: ignore
from core import config
from services.rag import query_vector_database
import json
import os

def _run_rag_query(query: str, llm: Any) -> str:
    """
    Runs a RAG query against the vector database and returns the results.
    """
    # query_vector_database is sync
    docs, _ = query_vector_database(query, llm)
    if docs:
        return docs
    return "No relevant information found in the knowledge base."

async def setup_tools(llm: Any) -> List[Any]:
    """Sets up and returns a list of tools, including MCP-based ones and RAG tool."""
    mcp_tools = []
    try:
        if not all(server.get('headers') and server['headers'].get('Authorization') for server in config.MCP_SERVERS.values()) or not config.MCP_SERVERS["github"]["headers"]["Authorization"]:
            print("❌ WARNING: MCP Authorization headers missing or invalid. Skipping MCP tool setup.")
        else:
            client = MultiServerMCPClient(config.MCP_SERVERS)
            mcp_tools = await client.get_tools()
            print(f"✅ MCP tools fetched successfully. Found {len(mcp_tools)} tools.")
    except Exception as e:
        print(f"❌ Error setting up MCP tools: {e}")

    # Create one RAG tool per source (namespace) so the agent can pick the right one
    sources = []
    sources_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sources.json")
    try:
        with open(sources_path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                sources = data
    except Exception as e:
        print(f"❌ Error reading sources.json for RAG tools: {e}")

    rag_tools: List[Any] = []
    for src in sources:
        resource_name = src.get("resource_name", "")
        description = src.get("resource_description", "")
        if not resource_name:
            continue
        tool = Tool(
            name=f"RAG_{resource_name}",
            func=lambda query, rn=resource_name: query_vector_database(query, llm, namespace=rn)[0],
            description=f"RAG over '{resource_name}'. {description}",
        )
        rag_tools.append(tool)

    return mcp_tools + rag_tools
