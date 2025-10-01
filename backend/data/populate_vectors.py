import argparse
import sys
import os
import json
import socket
from typing import List, Dict, Any, Optional, Tuple

from bs4 import BeautifulSoup # type: ignore
from langchain_community.document_loaders import (
    PyPDFDirectoryLoader, # type: ignore
    PyPDFLoader, # type: ignore
    UnstructuredURLLoader, # type: ignore
    RecursiveUrlLoader, # type: ignore
)
from langchain_chroma import Chroma # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain.schema.document import Document # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SOURCES_PATH = os.path.join(os.path.dirname(__file__), "sources.json")


def get_embedding_function():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


def _is_chroma_available() -> bool:
    host = "localhost"
    port = 8001
    try:
        with socket.create_connection((str(host), int(port)), timeout=2.0):
            return True
    except Exception:
        return False


def _get_chroma_client(collection_name: Optional[str] = None) -> Chroma:
    kwargs: Dict[str, Any] = {
        "host": "localhost",
        "port": 8001,
        "embedding_function": get_embedding_function(),
    }
    if collection_name:
        kwargs["collection_name"] = collection_name
    return Chroma(**kwargs) # type: ignore[arg-type]


def _read_sources_file() -> List[Dict[str, Any]]:
    if not os.path.exists(SOURCES_PATH):
        print(f"No sources file found at {SOURCES_PATH}")
        return []
    try:
        with open(SOURCES_PATH, 'r') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"Unable to parse {SOURCES_PATH}: {e}")
        return []
    if not isinstance(sources, list):
        print("sources.json must be a JSON array of resources")
        return []
    valid: List[Dict[str, Any]] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        rn = src.get("resource_name")
        rd = src.get("resource_description") or ""
        t = (src.get("type") or "").lower()
        p = src.get("path")
        if not rn or not t or not p:
            continue
        valid.append({
            "resource_name": rn,
            "resource_description": rd,
            "type": t,
            "path": p,
        })
    return valid


def list_sources() -> List[Dict[str, str]]:
    return [{"resource_name": s["resource_name"], "resource_description": s.get("resource_description", "")} for s in _read_sources_file()]


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


def load_documents_for_source(resource_name: str) -> List[Document]:
    src_meta = next((s for s in _read_sources_file() if s["resource_name"] == resource_name), None)
    if not src_meta:
        print(f"No source configured with resource_name='{resource_name}'")
        return []
    docs: List[Document] = []
    if src_meta["type"] == "pdf":
        docs = _load_from_pdf_path(src_meta["path"]) or []
    elif src_meta["type"] == "web":
        docs = _load_from_web_url(src_meta["path"]) or []
    for d in docs:
        d.metadata = d.metadata or {}
        d.metadata["resource_name"] = src_meta["resource_name"]
        d.metadata["resource_description"] = src_meta.get("resource_description", "")
    return docs


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


def add_to_chroma(chunks: List[Document], collection_name: str) -> Tuple[int, int]:
    db = _get_chroma_client(collection_name=collection_name)
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


def populate_source(resource_name: str) -> int:
    if not _is_chroma_available():
        print("⚠️ Chroma server is not reachable, skipping vector database population.")
        return 1
    documents = load_documents_for_source(resource_name)
    if not documents:
        print(f"No documents found for RAG population for source '{resource_name}'.")
        return 2
    chunks = split_documents(documents)
    existing, added = add_to_chroma(chunks, collection_name=resource_name)
    print(f"[{resource_name}] Chroma existing docs: {existing}, newly added: {added}")
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Populate Chroma collections by resource name.")
    parser.add_argument("resource_name", nargs="?", help="Name of the resource to populate. If omitted, populates all.")
    args = parser.parse_args(argv)

    if not _is_chroma_available():
        print("⚠️ Chroma server is not reachable, skipping vector database population.")
        return 1

    if args.resource_name:
        return populate_source(args.resource_name)

    sources = list_sources()
    if not sources:
        print("No sources configured. Nothing to populate.")
        return 0

    overall_code = 0
    for s in sources:
        rn = s.get("resource_name")
        if rn:
            code = populate_source(rn)
            if code != 0:
                overall_code = code
    return overall_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


