from typing import Dict, Any, Optional, List, Tuple
import socket
from langchain_chroma import Chroma # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain.prompts import ChatPromptTemplate # type: ignore
from langchain_core.language_models import BaseChatModel # type: ignore
from core import config

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_embedding_function():
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return embeddings


PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def _get_chroma_client(collection_name: Optional[str] = None) -> Chroma:
    # If a collection name is provided, use it to namespace documents
    kwargs: Dict[str, Any] = {
        "host": config.CHROMA_HOST,
        "port": int(config.CHROMA_PORT) if isinstance(config.CHROMA_PORT, str) else config.CHROMA_PORT,
        "embedding_function": get_embedding_function(),
    }
    if collection_name:
        kwargs["collection_name"] = collection_name
    return Chroma(**kwargs) # type: ignore[arg-type]

def _is_chroma_available() -> bool:
    host = config.CHROMA_HOST
    port = int(config.CHROMA_PORT) if isinstance(config.CHROMA_PORT, str) else config.CHROMA_PORT
    # Try a low-level TCP connect which is robust across versions
    try:
        with socket.create_connection((str(host), int(port)), timeout=2.0):
            return True
    except Exception:
        return False

def query_vector_database(query: str, llm: BaseChatModel, k: int = 4, namespace: Optional[str] = None):
    if not _is_chroma_available():
        return "Vector database is not available.", []

    # If a specific namespace/collection is provided, only search there
    db = _get_chroma_client(collection_name=namespace) if namespace else _get_chroma_client()
    results = db.similarity_search_with_score(query, k=k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query)

    response_text = llm.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    return response_text.content, sources

