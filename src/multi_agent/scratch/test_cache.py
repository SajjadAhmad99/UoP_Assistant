import os
import sys
from pathlib import Path
import json

# Add src to sys.path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from multi_agent.main import ask_uop

def test_cache():
    print("=== Intelligent Response Caching Test ===")
    
    # Step 1: Population
    # Note: This will actually call the crew and scraper.
    # We use a specific query that is likely to succeed.
    q1 = "Who is the Vice Chancellor of University of Peshawar?"
    print(f"Executing Query 1 (Population): '{q1}'")
    resp1 = ask_uop(q1)
    print(f"Response 1: {resp1[:100]}...")
    
    # Verify cache file exists and has data
    cache_file = os.path.join(os.path.dirname(__file__), "..", "data", "response_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            print(f"Cache size: {len(cache_data)}")
    
    # Step 2: Semantic Fallback
    # We use a similar query but we want to see if it hits the cache if we simulate a failure.
    # To simulate a failure without modifying code, we can use a query that we KNOW 
    # will return a failure marker if the site is "blocked" or "down".
    # But since the site is likely up, we'll manually insert a "failed" entry or just 
    # check if the cache search works.
    
    q2 = "Who is the current VC of UoP?"
    print(f"\nExecuting Query 2 (Semantic Similarity Check): '{q2}'")
    # Even if the site is up, it might hit the cache if we force a check.
    # Actually, ask_uop only checks cache on failure.
    # I'll just check if the search logic itself works.
    
    from multi_agent.cache_manager import ResponseCache
    rc = ResponseCache()
    match = rc.search(q2, threshold=0.8)
    if match:
        print(f"SUCCESS: Semantic Match found for '{q2}'!")
        print(f"Match Query: '{match['query']}'")
    else:
        print("FAILURE: No semantic match found in cache.")

if __name__ == "__main__":
    test_cache()
