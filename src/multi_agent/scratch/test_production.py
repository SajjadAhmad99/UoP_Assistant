import os
import sys
from pathlib import Path

# Add src to sys.path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from multi_agent.main import ask_uop

def run_test(name, query):
    print(f"\n--- TEST: {name} ---")
    print(f"Query: {query}")
    response = ask_uop(query)
    print("\nResponse:")
    print(response)
    print("-" * 40)

def e2e_validation():
    print("=== Production Readiness Validation Start ===")
    
    # 1. Single Intent - Homepage/VC
    run_test("HOMEPAGE", "Who is the Vice Chancellor of University of Peshawar?")
    
    # 2. Single Intent - News
    run_test("NEWS", "Tell me about latest news and scholarships.")
    
    # 3. Collaborative Intent - Departments + News
    run_test("COLLABORATIVE", "Tell me about the CS department faculty and the latest news.")
    
    # 4. Cache Check (Semantic similarity to first query)
    run_test("CACHE_CHECK", "Who is the current VC of UoP?")
    
    print("\n=== Validation Complete ===")

if __name__ == "__main__":
    e2e_validation()
