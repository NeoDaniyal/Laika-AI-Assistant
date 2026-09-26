"""
memory.py
=========
Handles extraction, storage, and retrieval of persistent user memories across chat sessions.
"""

import json
from typing import List, Dict, Optional
from backend.database import db
from backend.llm import ask_llm_stream

memories_collection = db["user_memories"]

EXTRACTION_PROMPT =  """You are a Memory Extraction System. Analyze the latest exchange between user and Assistant.
Determine if the user explicitly share long-term, persistant personal facts or explicit preferences.

QUALIFYING CATEGORIES TO EXTRACT:
- User identity/location (e.g., "Name is Daniyal", "Based in Pune")
- Technical Project preferences (e.g., "Prefers Python", "Building app name is Laika AI Assitant")
- Communication styles or constraints (e.g., "Prefers code without long long explanations")

DO NOT EXTRACT:
- Casual greetings, small talks, transient questions ("what is the capital of France?")
- One-off task request or debug logs

Output format MUST be valid JSON only with this schema:
{
"has_memory": true/false,
"memories":[
{
"category": "preference" | "identity" | "project",
"key": "unique_snake_case_key",
"value": "Consise factual statement"
}
]
}
If no new qualifying information is found, return: {"has_memory": false, "memories": []}

User Message: {user_message}
Assistant Response: {assistant_response}
"""

def extract_and_store_memories(user_message: str, assistant_response: str, user_id: str = "default_user"):
    """Background task to extract and upsert qualifying memories into MongoDB."""
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        ssistant_response=assistant_response
    )
    message = [
        {"role": "system", "content": "You output strictly raw JSON."},
        {"role": "user", "content": prompt}
    ]
    try:
        raw_ouput = ask_llm_stream(message)
        clean_json = raw_ouput.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        if data.get("has_memory") and data.get("memories"):
            for mem in data["memories"]:
                key = mem.get("key")
                val = mem.get("value")
                cat = mem.get("category", "general")

                if key and val:

                    memories_collection.update_one(
                        {"user_id": user_id, "key": key},
                        {"$set": {
                            "user_id": user_id,
                            "catogory": cat,
                            "key": key,
                            "value": val
                        }},
                        upsert=True
                    )
                    print(f"[Memory Persisted] ({key}): {val}")
    except Exception as e:
        print(f"[Memory Extraction Skipped/Failed]: {e}")

def retrieve_user_memories(user_id: str = "default_user")-> List[Dict[str, str]]:
    """Retrieves all active long-term memories for a user."""
    docs = memories_collection.find({"user_id": user_id})
    memories = []
    for doc in docs:
        memories.append({
            "key": doc["key"],
            "value": doc["value"]
        })
    return  memories

def format_memories_for_prompt(user_id: str = "default_user") -> str:
    """Formats stored memories into a system prompt injection block."""
    memories = retrieve_user_memories(user_id)
    if not memories:
        return ""

    formatted = "[User Long-Term Memory & Preferences]:\n"
    for mem in memories:
        formatted += f"- {mem['key']}: {mem['value']}\n"
    return formatted.strip()