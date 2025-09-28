from typing import List
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from models.chat import ChatMessage

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
