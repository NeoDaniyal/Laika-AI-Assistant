import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm import ask_llm_stream


async def test_llm_tool_calling():
    print("=== Testing LLM Tool Calling Pipeline ===")

    messages = [
        {"role": "system", "content": "You are Laika, an agentic AI assistant."},
        {"role": "user", "content": "What is 12 * 4?"},
    ]

    full_output = ""
    async for chunk in ask_llm_stream(messages):
        full_output += chunk

    print("\n--- Stream Output ---")
    print(full_output)
    print("---------------------\n")

    assert "calculator" in full_output
    assert "48" in full_output
    print("✓ Tool calling integration test passed successfully! 🎉")


if __name__ == "__main__":
    asyncio.run(test_llm_tool_calling())