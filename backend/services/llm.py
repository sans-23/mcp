from typing import Optional
from langchain_openai import ChatOpenAI # type: ignore

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
