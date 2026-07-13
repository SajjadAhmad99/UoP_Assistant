"""
RAG Indexer for UoP Knowledge Base
Creates a FAISS vector store from UOP_DATA.pdf for semantic search.

Usage:
    1. Place UOP_DATA.pdf in the project root directory
    2. Run: python src/multi_agent/tools/rag_indexer.py
    3. The faiss_index/ directory will be created/updated
"""
import os
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ── Configuration ────────────────────────────────────────────────────────────
DATA_PATH = "UOP_DATA.pdf"
INDEX_PATH = "faiss_index"

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"[{datetime.now()}] === UoP RAG Indexer ===")

    # Check if PDF exists
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: {DATA_PATH} not found!")
        print(f"Please place your UOP knowledge base PDF in the project root directory.")
        print(f"Expected location: {os.path.abspath(DATA_PATH)}")
        return False

    # Create index directory
    os.makedirs(INDEX_PATH, exist_ok=True)

    # Load PDF
    print(f"[{datetime.now()}] Loading PDF: {DATA_PATH}...")
    try:
        loader = PyPDFLoader(DATA_PATH)
        documents = loader.load()
        print(f"  Loaded {len(documents)} pages")
    except Exception as e:
        print(f"ERROR: Failed to load PDF: {e}")
        return False

    # Split into chunks
    print(f"[{datetime.now()}] Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=40,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"  Created {len(chunks)} chunks")

    # Load embeddings model
    print(f"[{datetime.now()}] Loading embeddings model...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        print("  Embeddings model loaded")
    except Exception as e:
        print(f"ERROR: Failed to load embeddings: {e}")
        return False

    # Create FAISS index
    print(f"[{datetime.now()}] Building FAISS index...")
    try:
        db = FAISS.from_documents(chunks, embeddings)
        print(f"  Index built with {len(db.index_to_doc)} vectors")
    except Exception as e:
        print(f"ERROR: Failed to build FAISS index: {e}")
        return False

    # Save index
    print(f"[{datetime.now()}] Saving index to {INDEX_PATH}/...")
    try:
        db.save_local(INDEX_PATH)
        print(f"[{datetime.now()}] SUCCESS: FAISS index created!")
        print(f"  Location: {os.path.abspath(INDEX_PATH)}")
        print(f"  Total documents: {len(db.index_to_doc)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save index: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
