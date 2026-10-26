from pathlib import Path

from io_loaders import load_jsonl
from normalize import normalize_record, dedupe, to_float, to_int, to_str, parse_ts

FIXTURES = Path(__file__).parent.parent / "fixtures"

def test_to_str():
    assert to_str("") is None
    assert to_str(None) is None
    assert to_str(" x ") == "x"


def test_parse_ts():
    assert parse_ts("") is None
    assert parse_ts("garbage") is None
    assert parse_ts("2026-10-19T14:00:05Z").minute == 0

def test_to_float_basic():
    assert to_float("640") == 640.0
    assert to_float(640) == 640.0
    assert to_float("1,234.5") == 1234.5


def test_to_float_blanks():
    assert to_float("n/a") is None
    assert to_float("") is None
    assert to_float(None) is None
    assert to_float(None, default=0.0) == 0.0


def test_to_int():
    assert to_int("42") == 42
    assert to_int("42.7") == 42
    assert to_int("n/a") is None
    assert to_int("n/a", default=0) == 0

def test_normalize_string_numbers():
    rec, warnings = normalize_record({
        "request_id": "x", "timestamp": "2026-10-19T14:00:09Z", "status": "200",
        "latency_ms": "640", "prompt_tokens": "980", "completion_tokens": "210",
        "error_code": "",
    })
    assert rec["status"] == 200
    assert rec["latency_ms"] == 640.0
    assert rec["prompt_tokens"] == 980
    assert rec["error_code"] is None
    assert warnings == []


def test_normalize_drops_bad_status():
    rec, warnings = normalize_record({"request_id": "x", "status": "oops"})
    assert rec is None
    assert len(warnings) == 1


def test_dirty_fixture_end_to_end():
    raw, errors = load_jsonl(FIXTURES / "logs_dirty.jsonl")
    assert len(raw) == 11
    assert len(errors) == 1

    records, warnings = [], []
    for r in raw:
        rec, w = normalize_record(r)
        warnings.extend(w)
        if rec is not None:
            records.append(rec)
    records, dup_warnings = dedupe(records)
    warnings.extend(dup_warnings)

    assert len(records) == 10
    assert sorted(w["request_id"] for w in warnings) == ["req_005", "req_007", "req_008"]
    first_008 = [r for r in records if r["request_id"] == "req_008"][0]
    assert first_008["latency_ms"] == 6400.0