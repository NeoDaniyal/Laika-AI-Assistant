"""
memory.py
=========
Handles extraction, deduplication, conflict resolution, and selective retrieval
of long-term user memories.
"""

import json
import re
from typing import List, Dict
from backend.database import db
from backend.llm import ask_llm_stream

memories_collection = db["user_memories"]

EXTRACTION_PROMPT = """You are a Memory Extraction & Management System.
Analyze the latest exchange between User and Assistant.

Determine if the User explicitly shared long-term, persistent personal facts, identity, or explicit preferences.

QUALIFYING CATEGORIES:
- identity (e.g., name, location, role)
- preference (e.g., favorite programming language, preferred response format)
- project (e.g., app name, tech stack, project goals)

IMPORTANT INSTRUCTIONS FOR UPDATES / CONFLICTS:
- If the user UPDATES an existing preference (e.g., "I switched from Python to Rust"), extract the NEW preference under the same logical key.
- Key names MUST be standardized snake_case (e.g., 'favorite_programming_language', 'current_project_name', 'user_location', 'communication_style').

Output format MUST be valid JSON only with this schema:
{{
  "has_memory": true/false,
  "memories": [
    {{
      "category": "preference" | "identity" | "project",
      "key": "standardized_snake_case_key",
      "value": "Concise updated factual statement",
      "importance": "high" | "medium" | "low"
    }}
  ]
}}

If no new qualifying information is found, return: {{"has_memory": false, "memories": []}}

User Message: {user_message}
Assistant Response: {assistant_response}
"""


async def extract_and_store_memories(user_message: str, assistant_response: str, user_id: str = "default_user"):
    """Extracts memories and performs deduplicated upserts in MongoDB."""
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        assistant_response=assistant_response
    )

    messages = [
        {"role": "system", "content": "You output strictly raw JSON."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw_result = ask_llm_stream(messages)
        raw_output = raw_result if isinstance(raw_result, str) else "".join(list(raw_result))

        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        if data.get("has_memory") and data.get("memories"):
            for mem in data["memories"]:
                key = mem.get("key")
                val = mem.get("value")
                cat = mem.get("category", "general")
                importance = mem.get("importance", "medium")

                if key and val:
                    # Upsert guarantees deduplication and updates existing keys automatically
                    await memories_collection.update_one(
                        {"user_id": user_id, "key": key},
                        {"$set": {
                            "user_id": user_id,
                            "category": cat,
                            "key": key,
                            "value": val,
                            "importance": importance
                        }},
                        upsert=True
                    )
                    print(f"[Memory Updated/Persisted] ({key}): {val}")

    except Exception as e:
        print(f"[Memory Extraction Skipped/Failed]: {e}")


async def retrieve_relevant_memories(user_query: str, user_id: str = "default_user", limit: int = 5) -> List[Dict[str, str]]:
    """
    Selectively retrieves memories matching the user query keywords, 
    plus high-importance identity memories.
    """
    # 1. Fetch HIGH importance core identity memories (always relevant)
    high_priority_cursor = memories_collection.find({
        "user_id": user_id,
        "importance": "high"
    })
    relevant_memories = await high_priority_cursor.to_list(length=10)
    seen_keys = {m["key"] for m in relevant_memories}

    # 2. Extract keywords from user query
    words = re.findall(r'\b\w{3,}\b', user_query.lower())
    ignore_words = {"what", "which", "where", "when", "your", "that", "this", "have", "with", "from", "build"}
    keywords = [w for w in words if w not in ignore_words]

    if keywords:
        # Build regex matching for key, value, or category
        regex_pattern = "|".join(keywords)
        keyword_cursor = memories_collection.find({
            "user_id": user_id,
            "$or": [
                {"key": {"$regex": regex_pattern, "$options": "i"}},
                {"value": {"$regex": regex_pattern, "$options": "i"}},
                {"category": {"$regex": regex_pattern, "$options": "i"}}
            ]
        })
        matching_docs = await keyword_cursor.to_list(length=limit)
        
        for doc in matching_docs:
            if doc["key"] not in seen_keys:
                relevant_memories.append(doc)
                seen_keys.add(doc["key"])

    return relevant_memories


async def format_relevant_memories_for_prompt(user_query: str, user_id: str = "default_user") -> str:
    """Formats only relevant memories into the context injection block."""
    memories = await retrieve_relevant_memories(user_query=user_query, user_id=user_id)
    if not memories:
        return ""

    formatted = "[Relevant User Memory & Preferences]:\n"
    for mem in memories:
        formatted += f"- {mem['key']}: {mem['value']}\n"
    return formatted.strip()