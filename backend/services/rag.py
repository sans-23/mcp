import os
import json
from typing import List, Tuple
import socket
import httpx # type: ignore
from bs4 import BeautifulSoup # type: ignore
from langchain_community.document_loaders import (
    PyPDFDirectoryLoader, # type: ignore
    PyPDFLoader, # type: ignore
    UnstructuredURLLoader, # type: ignore
    RecursiveUrlLoader, # type: ignore
)
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
from langchain.schema.document import Document # type: ignore
from langchain_chroma import Chroma # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain.prompts import ChatPromptTemplate # type: ignore
from langchain_core.language_models import BaseChatModel # type: ignore
from core import config

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Unified data directory with a declarative sources.json
DATA_DIR = "data"
SOURCES_PATH = "data/sources.json"


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


def _load_from_pdf_path(path: str) -> List[Document]:
    docs: List[Document] = []
    if os.path.isdir(path):
        loader = PyPDFDirectoryLoader(path)
        return loader.load()
    if path.endswith(".pdf") and os.path.exists(path):
        loader = PyPDFLoader(path)
        return loader.load()
    print(f"Skipping non-existent or non-pdf path: {path}")
    return docs


def _load_from_web_url(url: str) -> List[Document]:
    try:
        if "kubernetes.io/docs" in url:
            loader = RecursiveUrlLoader(
                url=url,
                max_depth=5,
                extractor=lambda x: BeautifulSoup(x, "html.parser").text,
                prevent_outside=True,
            )
            return loader.load()
        else:
            web_document_loader = UnstructuredURLLoader(urls=[url])
            return web_document_loader.load()
    except Exception as e:
        print(f"Error loading web source {url}: {e}")
        return []


def load_documents() -> List[Document]:
    documents: List[Document] = []

    if not os.path.exists(SOURCES_PATH):
        print(f"No sources file found at {SOURCES_PATH}")
        return documents

    try:
        with open(SOURCES_PATH, 'r') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"Unable to parse {SOURCES_PATH}: {e}")
        return documents

    if not isinstance(sources, list):
        print("sources.json must be a JSON array of resources")
        return documents

    for src in sources:
        if not isinstance(src, dict):
            continue
        resource_type = (src.get("type") or "").lower()
        path = src.get("path")
        if not path or not resource_type:
            continue

        if resource_type == "pdf":
            documents.extend(_load_from_pdf_path(path))
        elif resource_type == "web":
            documents.extend(_load_from_web_url(path))

    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def calculate_chunk_ids(chunks: List[Document]) -> List[Document]:
    last_page_id: str | None = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks


def _get_chroma_client() -> Chroma:
    return Chroma(
        host=config.CHROMA_HOST,
        port=int(config.CHROMA_PORT) if isinstance(config.CHROMA_PORT, str) else config.CHROMA_PORT,
        embedding_function=get_embedding_function(),
    )


def add_to_chroma(chunks: List[Document]) -> Tuple[int, int]:
    db = _get_chroma_client()

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[])
    existing_ids = set(existing_items.get("ids", []))

    new_chunks: List[Document] = [chunk for chunk in chunks_with_ids if chunk.metadata.get("id") not in existing_ids]

    added = 0
    if new_chunks:
        batch_size = 1000
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]
            new_chunk_ids = [chunk.metadata["id"] for chunk in batch]
            db.add_documents(batch, ids=new_chunk_ids)
            added += len(batch)

    return len(existing_ids), added


def _is_chroma_available() -> bool:
    host = config.CHROMA_HOST
    port = int(config.CHROMA_PORT) if isinstance(config.CHROMA_PORT, str) else config.CHROMA_PORT
    # Try a low-level TCP connect which is robust across versions
    try:
        with socket.create_connection((str(host), int(port)), timeout=2.0):
            return True
    except Exception:
        return False


def ensure_vector_database() -> None:
    if not _is_chroma_available():
        print("⚠️ Chroma server is not reachable, skipping vector database population.")
        return

    documents = load_documents()
    if not documents:
        print("No documents found for RAG population.")
        return

    try:
        chunks = split_documents(documents)
        existing, added = add_to_chroma(chunks)
        print(f"Chroma existing docs: {existing}, newly added: {added}")
    except Exception as e:
        print(f"❌ Failed to populate Chroma: {e}")


def query_vector_database(query: str, llm: BaseChatModel, k: int = 4):
    if not _is_chroma_available():
        return "Vector database is not available.", []
    db = _get_chroma_client()
    results = db.similarity_search_with_score(query, k=k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query)

    response_text = llm.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    return response_text.content, sources

