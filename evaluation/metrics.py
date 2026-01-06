def calculate_metrics(results, eval_cases):
    case_map = {c["id"]: c for c in eval_cases}

    refusal_correct = 0
    refusal_total = 0
    overconfident = 0

    for r in results:
        expected = case_map[r["id"]]

        if expected["should_refuse"]:
            refusal_total += 1
            if r["confidence"] == 0.0:
                refusal_correct += 1

        if not expected["should_refuse"]:
            if r["confidence"] > 0.7 and not r["movies"]:
                overconfident += 1

    return {
        "refusal_accuracy": refusal_correct / refusal_total if refusal_total else 1.0,
        "overconfidence_count": overconfident,
        "total_cases": len(results),
    }
