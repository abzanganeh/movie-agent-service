from time import time


def run_evaluation(agent_service, eval_cases):
    results = []

    for case in eval_cases:
        start = time()
        response = agent_service.chat(case["question"])
        latency_ms = int((time() - start) * 1000)

        refused = response.confidence == 0.0

        results.append({
            "id": case["id"],
            "question": case["question"],
            "refused": refused,
            "confidence": response.confidence,
            "movies": response.movies,
            "tools_used": response.tools_used,
            "latency_ms": latency_ms,
        })

    return results
