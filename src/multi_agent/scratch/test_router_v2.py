import os
import sys
from pathlib import Path

# Add src to sys.path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from multi_agent.crew import classify_query, IntentCategory

def test_router():
    queries = [
        "Who is the current Vice Chancellor of UOP?",
        "What are the hostel regulations?",
        "Tell me about the latest news and tenders.",
        "What is the fee for BS Computer Science?",
        "How many departments are in the Faculty of Life Sciences?",
        "Is there any scholarship for students?",
        "How to apply for private MA exams?",
        "Tell me about ORIC and research at UOP."
    ]

    print("=== Hybrid Router Refactor Test ===")
    for q in queries:
        intent = classify_query(q)
        print(f"Query: {q}")
        print(f"Resulting Intent: {intent.value}")
        print("-" * 30)

if __name__ == "__main__":
    test_router()
