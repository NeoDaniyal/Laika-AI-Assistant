
import json

with open(
    "backend/evaluation/chunk_export.json",
    "r",
    encoding="utf-8"
) as file:
    chunks = json.load(file)

print(f"Total chunks: {len(chunks)}")

for chunk in chunks:
    text = chunk.get("text", "")

    print("\n" + "=" * 60)
    print(f"Chunk: {chunk['chunk_index']}")
    print(f"Words: {chunk.get('word_count', 0)}")
    print(f"Preview: {text[:500]}")
