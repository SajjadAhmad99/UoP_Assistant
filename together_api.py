import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

response = client.chat.completions.create(
    model="meta-llama/llama-3-8b-instruct",
    messages=[
        {"role": "user", "content": "Hello from OpenRouter!"}
    ],
)

print(response.choices[0].message.content)
