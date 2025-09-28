from langchain_community.document_loaders import PyPDFLoader # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain_community.vectorstores import Chroma # type: ignore
from langchain_community.embeddings import HuggingFaceEmbeddings # type: ignore
from langchain.prompts import ChatPromptTemplate # type: ignore
from langchain_core.language_models import BaseChatModel # type: ignore
from core import config
import os

# This will be replaced by an online vector store in the future
CHROMA_DB_PATH = "./chroma_db"

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

async def populate_vector_database(pdf_path: str):
    if os.path.exists(CHROMA_DB_PATH):
        print(f"Chroma DB already exists at {CHROMA_DB_PATH}, skipping population.")
        return
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    splits = text_splitter.split_documents(documents)

    # Create a new Chroma DB from the documents
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=get_embedding_function(),
        persist_directory=CHROMA_DB_PATH
    )
    vectorstore.persist()
    print(f"Vector database populated with {len(splits)} chunks from {pdf_path}")

async def query_vector_database(query: str, llm: BaseChatModel, k: int = 4):
    
    vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=get_embedding_function())
    results = vectorstore.similarity_search_with_score(query, k=k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query)
    
    response_text = llm.invoke(prompt)

    sources = [doc.metadata.get("source", None) for doc, _score in results] # Assuming 'source' in metadata
    return response_text.content, sources

