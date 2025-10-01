import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
LLM_MODEL_NAME = "x-ai/grok-4-fast:free"

# --- MCP Server Configuration ---
MCP_SERVERS = {
    "github": {
        "transport": "streamable_http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            "Authorization": os.getenv("GITHUB_COPILOT_TOKEN")
        }
    }
}

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# --- ChromaDB Configuration ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")
