from fastapi import UploadFile
from sqlalchemy.orm import Session
from .. import models
import os
import shutil
from dotenv import load_dotenv

load_dotenv()
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_PERSIST_DIR = "data/chroma_db"

def get_vector_store():
    # Helper to get the Chroma DB instance
    embeddings = OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    )
    return Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embeddings)

async def process_and_store(file: UploadFile, user_id: int, db: Session):
    os.makedirs("data/uploads", exist_ok=True)
    file_location = f"data/uploads/{user_id}_{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    db_file = models.UploadedFile(
        filename=file.filename,
        filepath=file_location,
        content_type=file.content_type,
        owner_id=user_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Process for RAG
    if file.filename.endswith(".pdf"):
        loader = PyPDFLoader(file_location)
    else:
        # Fallback text loader
        loader = TextLoader(file_location, autodetect_encoding=True)
        
    documents = loader.load()
    
    # Add metadata for user separation
    for doc in documents:
        doc.metadata["user_id"] = str(user_id)
        doc.metadata["file_id"] = str(db_file.id)
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    if chunks:
        vectorstore = get_vector_store()
        vectorstore.add_documents(chunks)
        vectorstore.persist()
