import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from crewai import LLM

os.environ["NVIDIA_NIM_API_KEY"] = os.getenv("NVIDIA_NIM_API_KEY", "")

LLM_FAST = LLM(
    model='nvidia_nim/meta/llama3-70b-instruct',
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    temperature=0,
    max_tokens=50
)

try:
    res = LLM_FAST.call([{"role": "user", "content": "Reply exactly with 'hello'"}])
    print("SUCCESS LLM_FAST.call:")
    print(res)
except Exception as e:
    print("FAILED call:", e)
    import traceback
    traceback.print_exc()

