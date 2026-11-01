
import asyncio
import json
from bson import ObjectId

from backend.database import rag_chunks_collection

DOCUMENT_ID = "6ae6f0012b8514272d1adba5"
USER_ID = "6ae3f7c1d2a8bcaccdee7152"


async def inspect_chunks():
    chunks = await rag_chunks_collection.find(
        {
            "user_id": USER_ID,
            "document_id": ObjectId(DOCUMENT_ID)
        },
        {
            "_id": 0,
            "chunk_index": 1,
            "filename": 1,
            "word_count": 1,
            "text": 1
        }
    ).sort("chunk_index", 1).to_list(length=None)

    print(f"Total chunks found: {len(chunks)}")

    for chunk in chunks:
        print("\n" + "=" * 70)
        print(f"CHUNK INDEX: {chunk['chunk_index']}")
        print(f"FILENAME: {chunk.get('filename', 'Unknown')}")
        print(f"WORD COUNT: {chunk.get('word_count', 0)}")
        print("-" * 70)
        print(chunk.get("text", ""))

    # Save the complete output for easier inspection.
    with open(
        "backend/evaluation/chunk_export.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(chunks, file, indent=4, ensure_ascii=False)

    print("\nExport saved to backend/evaluation/chunk_export.json")


if __name__ == "__main__":
    asyncio.run(inspect_chunks())
