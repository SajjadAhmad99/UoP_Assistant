"""
Shared Embeddings Singleton — Performance Optimization
Eliminates the double-load of 'sentence-transformers/all-MiniLM-L6-v2'
that previously occurred independently in cache_manager.py and crew.py.
Both modules now reference this single instance, saving ~90MB RAM and ~8s startup.
"""
from __future__ import annotations
import threading
from typing import Optional

_lock = threading.Lock()
_model = None


def get_embeddings_model():
    """
    Return the shared HuggingFace embeddings model instance.
    Thread-safe lazy initialization — model is loaded only once.
    """
    global _model
    if _model is None:
        with _lock:
            if _model is None:  # double-checked locking
                from langchain_huggingface import HuggingFaceEmbeddings
                print("[EmbeddingsSingleton] Loading sentence-transformers/all-MiniLM-L6-v2 (one-time load)...")
                _model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
                print("[EmbeddingsSingleton] Model ready.")
    return _model
