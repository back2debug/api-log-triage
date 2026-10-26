from pathlib import Path

import pytest

from io_loaders import load_jsonl
from metrics import group_stats, peak_per_minute
from normalize import normalize_record, dedupe

FIXTURES = Path(__file__).parent.parent / "fixtures"


def clean_dirty_records():
    raw, _ = load_jsonl(FIXTURES / "logs_dirty.jsonl")
    records = [rec for rec, _ in map(normalize_record, raw) if rec is not None]
    records, _ = dedupe(records)
    return records


def test_group_stats_empty():
    stats = group_stats([])
    assert stats["request_count"] == 0
    assert stats["error_rate"] is None
    assert stats["p50_latency_ms"] is None


def test_group_stats_proj_fin_a_gpt4o():
    records = [r for r in clean_dirty_records()
               if r["project_id"] == "proj_fin_a" and r["model"] == "gpt-4o"]
    stats = group_stats(records)
    assert stats["request_count"] == 5
    assert stats["success_count"] == 3
    assert stats["error_rate"] == 0.4
    assert stats["p50_latency_ms"] == 812.0
    assert stats["p95_latency_ms"] == pytest.approx(5841.2)
    assert stats["p99_latency_ms"] == pytest.approx(6288.24)
    assert stats["total_tokens"] == 5162
    assert stats["rate_limit_errors"] == 2

def test_peak_per_minute_empty():
    assert peak_per_minute([]) == 0
    assert peak_per_minute([(None, 1)]) == 0


def test_peak_rpm_and_tpm_proj_fin_a():
    records = [r for r in clean_dirty_records() if r["project_id"] == "proj_fin_a"]
    peak_rpm = peak_per_minute((r["timestamp"], 1) for r in records)
    peak_tpm = peak_per_minute(
        (r["timestamp"], r["prompt_tokens"] + r["completion_tokens"]) for r in records)
    assert peak_rpm == 3
    assert peak_tpm == 2740