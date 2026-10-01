import asyncio
import queue
import threading
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.database import chats_collection
from backend.llm import ask_llm_stream
from backend.prompts import build_system_message
from backend.context import build_context
from backend.memory import extract_and_store_memories 
app = FastAPI(title="AI Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    chat_id: Optional[str] = None
    messages: List[MessageItem]


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        # 1. Convert Pydantic models to dicts
        history = [msg.model_dump() for msg in request.messages]

        # 2. Extract system message string
        sys_str = build_system_message()
        full_history = [{"role": "system", "content": sys_str}] + history

        # 3. Fetch existing summary from MongoDB if available
        existing_summary = ""
        if request.chat_id and ObjectId.is_valid(request.chat_id):
            chat_doc = await chats_collection.find_one({"_id": ObjectId(request.chat_id)})
            if chat_doc:
                existing_summary = chat_doc.get("summary", "")

        # 4. Build context with summarization pipeline
        context_data = await build_context(
            messages=full_history,
            existing_summary=existing_summary,
            max_tokens=3000
        )
        truncated_history = context_data["messages"]
        updated_summary = context_data["summary"]

        # 5. Thread-safe Queue and SENTINEL signal definition
        token_queue = queue.Queue()
        SENTINEL = object()  # Sentinel token indicating the thread is finished

        def generate_tokens_in_thread():
            """Worker thread running the blocking LLM generator."""
            try:
                for token in ask_llm_stream(truncated_history):
                    token_queue.put(token)
            except Exception as e:
                token_queue.put(f"\n[Stream Error: {str(e)}]")
            finally:
                token_queue.put(SENTINEL)

        # Start LLM fetching in a separate daemon thread
        threading.Thread(target=generate_tokens_in_thread, daemon=True).start()

        # 6. Async generator yielding tokens to FastAPI StreamingResponse
        async def async_token_stream():
            full_response = ""
            while True:
                try:
                    # Get next token from thread queue without blocking asyncio
                    token = await asyncio.to_thread(token_queue.get, timeout=0.1)
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue

                # Stop when sentinel object is received
                if token is SENTINEL:
                    break

                full_response += token
                yield token

            # Save complete response and updated summary to MongoDB
            if request.chat_id and ObjectId.is_valid(request.chat_id):
                user_msg = history[-1]
                ai_msg = {"role": "assistant", "content": full_response}

                chat = await chats_collection.find_one({"_id": ObjectId(request.chat_id)})
                update_query = {
                    "$push": {"messages": {"$each": [user_msg, ai_msg]}},
                    "$set": {"summary": updated_summary}
                }

                if chat and len(chat.get("messages", [])) == 0:
                    title_snippet = user_msg["content"][:25] + ("..." if len(user_msg["content"]) > 25 else "")
                    update_query["$set"]["title"] = title_snippet

                await chats_collection.update_one(
                    {"_id": ObjectId(request.chat_id)},
                    update_query
                )
                if request.messages:
                    user_last_prompt = request.messages[-1].content
                    threading.Thread(
                    target=extract_and_store_memories,
                    args=(user_last_prompt, full_response),
                    daemon=True
                    ).start()

        return StreamingResponse(async_token_stream(), media_type="text/plain")

    except Exception as e:
        print(f"Error in chat_stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats")
async def get_chats():
    chats = []
    cursor = chats_collection.find({}, {"messages": 0}).sort("created_at", -1)
    async for doc in cursor:
        chats.append({"id": str(doc["_id"]), "title": doc.get("title", "New Conversation")})
    return chats


@app.get("/chats/{chat_id}")
async def get_chat_history(chat_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid Chat ID")

    chat = await chats_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    cleaned_messages = []
    for msg in chat.get("messages", []):
        cleaned_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })

    return {"id": str(chat["_id"]), "messages": cleaned_messages}