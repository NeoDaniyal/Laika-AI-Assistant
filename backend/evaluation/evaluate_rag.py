import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.vector_search import search_similar_chunks


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "rag_dataset.json"
RESULTS_DIR = BASE_DIR / "results"
REPORT_PATH = RESULTS_DIR / "rag_report.json"

USER_ID = os.getenv("RAG_EVAL_USER_ID")
SCORE_THRESHOLD = float(
    os.getenv("RAG_EVAL_SCORE_THRESHOLD", "0.45")
)

K_VALUES = [1, 2, 5, 8]


def calculate_recall(retrieved_indices, relevant_indices, k):
    relevant = set(relevant_indices)
    retrieved = set(retrieved_indices[:k])

    if not relevant:
        return 0.0

    return len(retrieved & relevant) / len(relevant)


def calculate_reciprocal_rank(retrieved_indices, relevant_indices):
    relevant = set(relevant_indices)

    for rank, chunk_index in enumerate(retrieved_indices, start=1):
        if chunk_index in relevant:
            return 1.0 / rank

    return 0.0


async def evaluate_test_case(test_case):
    query = test_case["query"]
    document_id = test_case["document_id"]
    relevant_indices = test_case["relevant_chunk_indices"]

    start_time = time.perf_counter()

    retrieved_chunks = await search_similar_chunks(
        query=query,
        user_id=USER_ID,
        top_k=8,
        score_threshold=SCORE_THRESHOLD,
        document_ids=[document_id]
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    retrieved_indices = [
        chunk["chunk_index"]
        for chunk in retrieved_chunks
    ]
    
    relevant_chunk_ranks = {
        chunk_index: (
            retrieved_indices.index(chunk_index) + 1
            if chunk_index in retrieved_indices
            else None
        )
        for chunk_index in relevant_indices
    }
    
    metrics = {
        f"recall@{k}": calculate_recall(
            retrieved_indices,
            relevant_indices,
            k
        )
        for k in K_VALUES
    }

    metrics["mrr"] = calculate_reciprocal_rank(
        retrieved_indices,
        relevant_indices
    )

    return {
        "test_id": test_case["test_id"],
        "query": query,
        "expected_chunks": relevant_indices,
        "retrieved_chunks": retrieved_indices,
        "relevant_chunk_ranks": relevant_chunk_ranks,
        "similarity_scores": [
            chunk["score"] for chunk in retrieved_chunks
        ],
        "latency_ms": round(latency_ms, 2),
        "metrics": metrics
    }


async def main():
    if not USER_ID:
        raise ValueError(
            "Set RAG_EVAL_USER_ID before running the evaluator."
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not dataset:
        raise ValueError("Evaluation dataset is empty.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    print(f"Starting RAG evaluation: {len(dataset)} test cases")
    print(f"Similarity threshold: {SCORE_THRESHOLD}")

    for index, test_case in enumerate(dataset, start=1):
        print(
            f"\n[{index}/{len(dataset)}] "
            f"{test_case['test_id']}: {test_case['query']}"
        )

        result = await evaluate_test_case(test_case)
        results.append(result)

        print("Expected:", result["expected_chunks"])
        print("Retrieved:", result["retrieved_chunks"])
        print("Relevant chunk ranks:", result["relevant_chunk_ranks"])
        print("Metrics:", result["metrics"])
        print("Latency:", result["latency_ms"], "ms")

    metric_names = [
        "recall@1",
        "recall@2",
        "recall@5",
        "recall@8",
        "mrr"
    ]

    averages = {
        metric: round(
            sum(r["metrics"][metric] for r in results) / len(results),
            4
        )
        for metric in metric_names
    }

    average_latency = round(
        sum(r["latency_ms"] for r in results) / len(results),
        2
    )

    report = {
        "evaluation_date": datetime.now(timezone.utc).isoformat(),
        "total_test_cases": len(results),
        "user_id": USER_ID,
        "score_threshold": SCORE_THRESHOLD,
        "average_latency_ms": average_latency,
        "average_metrics": averages,
        "results": results
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 55)
    print("RAG EVALUATION SUMMARY")
    print("=" * 55)

    for metric, score in averages.items():
        print(f"{metric}: {score:.4f}")

    print(f"Average latency: {average_latency} ms")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())