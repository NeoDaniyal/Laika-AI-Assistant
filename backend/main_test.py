from pymongo import MongoClient
from bson import ObjectId

# Connect synchronously using standard PyMongo
client = MongoClient("mongodb://localhost:27017/") # Or your MongoDB connection string if different
db = client["ai_chatbot"] # Ensure this matches your database name
rag_chunks_collection = db["rag_chunks"]

document_id = "6ae6f5ad6c57e7af55e014f5"

# Convert string ID to ObjectId if your database stores them as ObjectIds
try:
    obj_id = ObjectId(document_id)
except Exception:
    obj_id = document_id

# Synchronous find and list conversion works perfectly here
chunks = list(
    rag_chunks_collection.find(
        {"document_id": obj_id}
    ).sort("chunk_index", 1)
)

print(f"\nFound {len(chunks)} chunks for document {document_id}\n")

for chunk in chunks:
    print("\n" + "=" * 60)
    print(f"CHUNK INDEX: {chunk.get('chunk_index')}")
    print("=" * 60)
    print(chunk.get("text"))