from typing import List
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from models.chat import ChatMessage

def db_messages_to_lc_messages(history_records: List[ChatMessage]) -> List[BaseMessage]:
    """Converts a list of ChatMessage DB objects to LangChain's BaseMessage list."""
    lc_messages = []
    for rec in history_records:
        if not rec.content:
            continue
            
        # Handle both old string content and new LLMOutputBlock content
        if isinstance(rec.content, dict) and "blocks" in rec.content:
            # New structured content
            content_blocks = rec.content["blocks"]
            content_text = " ".join([block["text"] for block in content_blocks if block["block_type"] == "text"])
        elif isinstance(rec.content, dict) and "text" in rec.content:
            # Old unstructured content
            content_text = rec.content["text"]
        else:
            # Fallback for unexpected content formats
            content_text = str(rec.content)

        if rec.role.lower() == "user":
            lc_messages.append(HumanMessage(content=content_text))
        elif rec.role.lower() == "ai":
            lc_messages.append(AIMessage(content=content_text))
    return lc_messages
