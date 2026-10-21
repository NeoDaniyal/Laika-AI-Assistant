import json
import re
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import AsyncGenerator, Dict, Any, List
from backend.tools import registry

load_dotenv()

client = AsyncOpenAI(
    base_url="https://api.inceptionlabs.ai/v1/",
    api_key=os.getenv("HF_TOKEN")
)

def format_tool_instructions() -> str:
    """Generates prompt instructions describing available tools to the LLM."""
    schemas = registry.to_schemas()
    if not schemas:
        return ""

    instructions = (
        "\n\nYou have access to the following tools:\n"
        f"{json.dumps(schemas, indent=2)}\n\n"
        "If you need to perform a calculation or run a tool to answer the user's request, "
        "respond ONLY with a tool call formatted strictly as JSON as follows:\n"
        '```tool_call\n{"name": "<tool_name>", "arguments": {<arguments>}}\n```\n'
        "Do not include extra text when issuing a tool call. "
        "If no tool call is needed, answer the prompt normally."
    )
    return instructions


async def ask_llm_stream(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """Streams responses from the LLM, catching and executing tool calls when requested."""

    # 1. Augment system message with tool schemas
    tool_instructions = format_tool_instructions()
    augmented_messages = [msg.copy() for msg in messages]

    if augmented_messages and augmented_messages[0].get("role") == "system":
        augmented_messages[0]["content"] += tool_instructions
    else:
        augmented_messages.insert(0, {"role": "system", "content": tool_instructions})

    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    # 2. Check for Calculator Tool Trigger
    math_match = re.search(
        r"(\d+(?:\.\d+)?)\s*([\+\-\*/×÷])\s*(\d+(?:\.\d+)?)", last_user_msg
    )

    if math_match:
        a_val, op_symbol, b_val = math_match.groups()
        op_map = {
            "+": "add",
            "-": "subtract",
            "*": "multiply",
            "×": "multiply",
            "/": "divide",
            "÷": "divide",
        }
        operation = op_map.get(op_symbol)

        if operation:
            try:
                tool_args = {"operation": operation, "a": float(a_val), "b": float(b_val)}
                result = registry.execute("calculator", tool_args)
                yield f"*(Executing tool `calculator` with arguments `{json.dumps(tool_args)}`)*\n\n"
                yield f"The result of {a_val} {op_symbol} {b_val} is **{result}**."
                return
            except Exception as e:
                yield f"\n[Tool Execution Error: {str(e)}]\n"

    # 3. Check for Image Generation Tool Trigger
    image_keywords = ["generate an image", "create an image", "draw", "generate image", "image of"]
    is_image_query = any(kw in last_user_msg.lower() for kw in image_keywords)

    if is_image_query:
        clean_prompt = re.sub(
            r"^(generate an image of|create an image of|generate image of|draw an image of|draw|generate an image|create an image)\s*",
            "",
            last_user_msg,
            flags=re.IGNORECASE,
        ).strip()
        if not clean_prompt:
            clean_prompt = last_user_msg

        tool_args = {"prompt": clean_prompt}
        yield f"*(Executing tool `image_generation` with arguments `{json.dumps(tool_args)}`)*\n\n"

        try:
            result_msg = registry.execute("image_generation", tool_args)
            
            # Extract local relative path and convert Windows backslashes (\) to web forward slashes (/)
            if "saved at: " in result_msg:
                raw_path = result_msg.split("saved at: ")[-1].strip()
                web_path = raw_path.replace("\\", "/")
                image_url = f"http://localhost:8000/{web_path}"
                
                yield f"🎨 Here is your generated image:\n\n![{clean_prompt}]({image_url})"
            else:
                yield f"🎨 {result_msg}"
            return
        except Exception as e:
            yield f"\n[Image Generation Error: {str(e)}]\n"
            return

    # 4. Check for Web Search Tool Trigger
    search_keywords = ["search", "latest", "news", "find", "lookup", "who is", "what is the current"]
    is_search_query = any(kw in last_user_msg.lower() for kw in search_keywords) and not math_match

    if is_search_query:
        clean_query = re.sub(r"^(search for|search|lookup|find)\s+", "", last_user_msg, flags=re.IGNORECASE).strip()
        if not clean_query:
            clean_query = last_user_msg

        tool_args = {"query": clean_query, "max_results": 3}
        yield f"*(Executing tool `web_search` with arguments `{json.dumps(tool_args)}`)*\n\n"

        try:
            search_results = registry.execute("web_search", tool_args)

            if search_results:
                yield f"Here are the latest search updates for **'{clean_query}'**:\n\n"

                source_list = []
                for idx, item in enumerate(search_results, start=1):
                    title = item.get("title", "No Title")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "#")
                    yield f"**{idx}. [{title}]({link})**\n{snippet}\n\n"

                    source_list.append({
                        "source": title[:30] + ("..." if len(title) > 30 else ""),
                        "chunk": idx,
                        "score": 0.95,
                        "url": link,
                        "snippet": snippet
                    })

                yield f"\n__SOURCES_JSON__:{json.dumps(source_list)}"
            else:
                yield "No web search results were found for your query."
            return
        except Exception as e:
            yield f"\n[Web Search Execution Error: {str(e)}]\n"
            return


# 5. Standard conversational streaming through the actual LLM
    try:
        response = await client.chat.completions.create(
            model="mercury-3",
            messages=augmented_messages,
            max_tokens=1024,
            stream=True,
        )

        for chunk in response:
            if chunk.choices:
                content = chunk.choices[0].delta.content

                if content:
                    yield content

    except Exception as e:
        print(f"Error in ask_llm_stream: {e}")
        yield f"\n[Error streaming response: {str(e)}]"
