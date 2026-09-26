import os
from typing import Dict, List, Generator
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

def ask_llm_stream(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            max_tokens=1024,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    yield delta.content

    except Exception as e:
        print(f"Error in ask_llm_stream: {e}")
        yield f"\n[Error streaming response: {str(e)}]"