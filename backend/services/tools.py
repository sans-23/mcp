from typing import List, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from core import config

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
