import os
import sys
from pathlib import Path

# Add src to sys.path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from multi_agent.main import ask_uop

def test_collaboration():
    print("=== Multi-Agent Collaborative Routing Test ===")
    
    # Query involving both Homepage (VC) and News
    q = "Who is the Vice Chancellor and tell me about latest news."
    print(f"Executing Multi-Intent Query: '{q}'")
    
    response = ask_uop(q)
    print("\n--- FINAL COLLABORATIVE RESPONSE ---")
    print(response)
    print("--------------------------------------")

if __name__ == "__main__":
    test_collaboration()
