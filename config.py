"""
Configuration file for University Chatbot System
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY")

# Model Configuration
LLM_MODEL = "groq/llama-3.1-8b-instant"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# University Specific
UNIVERSITY_NAME = "University of Peshawar"
UNIVERSITY_DOMAINS = ["uop.edu.pk", "peshawar.edu.pk"]

# URLs for Scraping
UNIVERSITY_URLS = {
    "admission": "https://www.uop.edu.pk/admissions/",
    "exams": "https://www.uop.edu.pk/examinations/",
    "fees": "https://www.uop.edu.pk/fee-structure/",
    "departments": "https://www.uop.edu.pk/departments/",
    "merit": "https://www.uop.edu.pk/merit-list/"
}

# Agent Configuration
AGENT_CONFIG = {
    "temperature": 0.1,
    "max_tokens": 1000,
    "verbose": True
}

# RAG Configuration
RAG_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "similarity_top_k": 3
}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
CACHE_DIR = os.path.join(DATA_DIR, "cache")