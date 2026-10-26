import math

def safe_div(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator

def percentile(values, p):
    """Linear-interpolation percentile, p in [0, 100]. None for empty input."""
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    rank = (p / 100.0) * (len(xs) - 1)
    lo, hi = math.floor(rank), math.ceil(rank)
    if lo == hi:
        return xs[int(rank)]
    return xs[lo] + (rank - lo) * (xs[hi] - xs[lo])

def is_success(status):
    return 200 <= status < 300

def group_stats(records):
    request_count = len(records)
    successes = [r for r in records if is_success(r["status"])]
    success_count = len(successes)
    error_count = request_count - success_count
    latencies = [r["latency_ms"] for r in successes]

    return {
        "request_count": request_count,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate": safe_div(error_count, request_count),
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "p99_latency_ms": percentile(latencies, 99),
        "total_tokens": sum(r["prompt_tokens"] + r["completion_tokens"] for r in records),
        "rate_limit_errors": sum(1 for r in records if r["status"] == 429),
    }

