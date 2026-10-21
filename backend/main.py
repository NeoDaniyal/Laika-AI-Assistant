import os
import json
import shutil
import traceback
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from backend.database import chats_collection
from backend.llm import ask_llm_stream
from backend.prompts import build_system_message
from backend.context import build_context
from backend.memory import extract_and_store_memories 
from backend.rag import ingest_document
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

app.mount("/generated_images", StaticFiles(directory=IMAGE_DIR), name="generated_images")

class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    chat_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    messages: List[MessageItem]


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        # 1. Convert Pydantic models to dicts
        history = [msg.model_dump() for msg in request.messages]
        user_id = request.user_id or "default_user"
        chat_id = request.chat_id

        user_last_msg = history[-1]["content"] if history else ""

        if not chat_id:
            title_snippet = user_last_msg[:25] + ("..." if len(user_last_msg) > 25 else "")
            new_chat = {
                "title": title_snippet or "New Conversation",
                "messages": [],
                "summary": "",
                "user_id": user_id,
                "created_at": datetime.utcnow(),
            }
            result = await chats_collection.insert_one(new_chat)
            chat_id = str(result.inserted_id)
        # 2. Extract system message string
        sys_str = build_system_message()
        full_history = [{"role": "system", "content": sys_str}] + history

        # 3. Fetch existing summary from MongoDB if available
        existing_summary = ""
        if chat_id and ObjectId.is_valid(chat_id):
            chat_doc = await chats_collection.find_one({"_id": ObjectId(chat_id)})
            if chat_doc:
                existing_summary = chat_doc.get("summary", "")

        # 4. Build context (includes memory, active session summary, and RAG retrieval)
        context_data = await build_context(
            messages=full_history,
            existing_summary=existing_summary,
            max_tokens=3000,
            user_id=user_id,
            enable_rag=True
        )
        
        truncated_history = context_data["messages"]
        updated_summary = context_data["summary"]
        retrieved_chunks = context_data.get("retrieved_chunks", [])

        # 5. SSE Event Generator for Token & Source Citation Streaming
        async def event_generator():
            full_response = ""

            yield f"event: chat_id\ndata: {json.dumps({'chat_id': chat_id})}\n\n"
            # Stream LLM generated tokens
            try:
                async for token in ask_llm_stream(truncated_history):
                    full_response += token
                    event_payload = json.dumps({"content": token})
                    yield f"event: token\ndata: {event_payload}\n\n"
            except TypeError:
                async for token in ask_llm_stream(truncated_history):
                    full_response += token
                    event_payload = json.dumps({"content": token})
                    yield f"event: token\ndata: {event_payload}\n\n"

            # Stream RAG Source Citations metadata if documents were retrieved
            if retrieved_chunks:
                sources_payload = json.dumps([
                    {
                        "source": chunk.get("filename", "Unknown"),
                        "chunk": chunk.get("chunk_index", 0),
                        "score": round(chunk.get("score", 0.0), 4)
                    }
                    for chunk in retrieved_chunks
                ])
                yield f"event: sources\ndata: {sources_payload}\n\n"

            # Save completed response, summary, and trigger memory extraction
            if chat_id and ObjectId.is_valid(chat_id):
                user_msg = history[-1]

                final_content = full_response
                extracted_sources = []

                if "__SOURCES_JSON__:" in full_response:
                    parts = full_response.split("__SOURCES_JSON__:")
                    final_content = parts[0].strip()
                    try:
                        extracted_sources = json.loads(parts[1].strip())
                    except Exception as err:
                        print(f"Error parsing sources for DB save: {err}")

                ai_msg = {"role": "assistant", "content": final_content, "sources": extracted_sources}

                chat = await chats_collection.find_one({"_id": ObjectId(chat_id)})
                update_query = {
                    "$push": {"messages": {"$each": [user_msg, ai_msg]}},
                    "$set": {"summary": updated_summary}
                }

                if chat and len(chat.get("messages", [])) == 0:
                    title_snippet = user_msg["content"][:25] + ("..." if len(user_msg["content"]) > 25 else "")
                    update_query["$set"]["title"] = title_snippet

                await chats_collection.update_one(
                    {"_id": ObjectId(chat_id)},
                    update_query
                )

                if request.messages:
                    user_last_prompt = request.messages[-1].content
                    await extract_and_store_memories(user_last_prompt, final_content, user_id=user_id)

            # Signal stream completion
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

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
            "content": msg.get("content", ""),
            "sources": msg.get("sources", [])
        })

    return {"id": str(chat["_id"]), "messages": cleaned_messages}


UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_file(
    files: List[UploadFile] = File(...),
    user_id: str = Form("default_user")
):
    try:
        total_chunks = 0
        uploaded_summary = []
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "txt"

        print(f"📥 Received file for ingestion: {file.filename} (Type: {ext})")
        # Ingest the uploaded document into the RAG vector store
        ingest_result = await ingest_document(
            file_path=file_path,
            filename=file.filename,
            file_type=ext,
            user_id=user_id
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        chunks = ingest_result.get("chunks_created", 0)
        total_chunks += chunks
        uploaded_summary.append({"name": file.filename, "chunks": chunks})

        return {
            "message": f"Successfully uploaded and ingested {len(files)} file(s).",
            "files": uploaded_summary,
            "total_chunks": total_chunks
        }
    except Exception as e:
        print(f"Error in upload_files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RenameChatRequest(BaseModel):
    title: str

@app.patch("/chats/{chat_id}")
async def rename_chat(chat_id: str, request: RenameChatRequest):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    result = await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"title": request.title}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"message": "Chat renamed successfully"}

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    result = await chats_collection.delete_one({"_id": ObjectId(chat_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"message": "Chat deleted successfully"}
    