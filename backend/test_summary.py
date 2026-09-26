"""
test_summary.py
===============
Test harness for verifying conversation summarization logic.
"""

from context import build_context, estimate_tokens
from summarizer import summarize_messages


def test_summarization_pipeline():
    print("=" * 60)
    print("RUNNING SUMMARIZATION PIPELINE TEST")
    print("=" * 60)

    # 1. Mock a conversation history that exceeds token limits
    system_prompt = {
        "role": "system",
        "content": "You are Laika Assistant, created by Daniyal."
    }

    # Simulate a long back-and-forth conversation
    long_history = [
        system_prompt,
        {"role": "user", "content": "Hi, my name is Daniyal. I am a software engineer working on an AI chatbot in Pune."},
        {"role": "assistant", "content": "Nice to meet you Daniyal! How can I help with your chatbot project?"},
        {"role": "user", "content": "I am using React for the frontend, FastAPI for backend, and MongoDB for data storage."},
        {"role": "assistant", "content": "That is a solid modern stack. MongoDB pairs very well with FastAPI."},
        {"role": "user", "content": "I prefer detailed technical code snippets rather than high-level explanations."},
        {"role": "assistant", "content": "Understood. I will provide direct code implementations."},
        {"role": "user", "content": "Now I am testing if the context window will summarize this older information correctly."},
        {"role": "assistant", "content": "I am monitoring context usage to see if older turns get compressed."},
        # Recent turns (should remain un-summarized at the end)
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What were my key preferences and stack details mentioned earlier?"}
    ]

    # Calculate initial token estimate
    total_raw_tokens = sum(estimate_tokens(m["content"]) for m in long_history)
    print(f"\n[Raw History Count]: {len(long_history) - 1} messages")
    print(f"[Estimated Raw Tokens]: ~{total_raw_tokens} tokens")

    # 2. Force trigger by setting max_tokens low (e.g., 100 tokens)
    print("\n--- Triggering build_context (Threshold: 100 tokens) ---")
    context_output = build_context(
        messages=long_history,
        existing_summary="",
        max_tokens=100  # Low threshold forces summarization
    )

    result_messages = context_output["messages"]
    summary = context_output["summary"]
    summarized_flag = context_output["summarized_new_chunks"]

    # 3. Print Results
    print(f"\n[Summarization Triggered]: {summarized_flag}")
    print(f"\n[Generated Summary]:\n>>> {summary}\n")

    print("[Final Context Window Payload Passed to LLM]:")
    for idx, msg in enumerate(result_messages):
        role_label = f"[{msg['role'].upper()}]"
        preview = msg['content'][:80] + ("..." if len(msg['content']) > 80 else "")
        print(f"  {idx + 1}. {role_label:<12} {preview}")

    # 4. Verification Assertions
    assert summarized_flag is True, "Summarization should have been triggered."
    assert len(summary) > 0, "Summary string should not be empty."
    assert result_messages[1]["role"] == "system", "Second message should be summary system message."
    assert "Conversation Summary" in result_messages[1]["content"], "Summary marker missing."
    
    print("\n✅ TEST PASSED: Summarization pipeline functioning as expected!")
    print("=" * 60)


if __name__ == "__main__":
    test_summarization_pipeline()