import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    
    # CrewAI Configuration
    CREWAI_MAX_ITER = int(os.getenv("CREWAI_MAX_ITER", 3))
    
    # Vector Store
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./vector_store")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # University Specific
    UNIVERSITY_NAME = "University of Peshawar"
    
    # Website URLs for Scraping
    ADMISSION_URL = "http://www.uop.edu.pk/admissions/"
    EXAMINATION_URL = "http://www.uop.edu.pk/examinations/"
    FEE_URL = "http://www.uop.edu.pk/fee-structure/"
    MERIT_URL = "http://www.uop.edu.pk/merit-list/"
    
settings = Settings()