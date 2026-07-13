import os
import sys

# Load environment variable
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.multi_agent.crew import classify_query

queries = [
    "who is the current vc?", # Keyword match -> homepage
    "I want to incubate my startup idea", # Keyword match (incubation) -> student_corner
    "what is the meaning of life?", # Fallback to LLM -> facts
    "show me the structure of the english department", # Keyword match (department) -> department
]

for q in queries:
    print(f"\nQuery: {q}")
    print(f"Result: {classify_query(q)}")
