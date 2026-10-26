from datetime import datetime, timezone

BLANKS = {"", "null", "none", "na", "n/a", "-", "nan", "undefined"}

def to_float(value, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if s.lower() in BLANKS:
        return default
    try:
        return float(s)
    except ValueError:
        return default

def to_int(value, default=None):
    f = to_float(value)
    return default if f is None else int(f)

def to_str(value, default=None):
    s = str(value).strip().replace(",", "")
    if s.lower() in BLANKS:
        return default

def to_str(value):
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in BLANKS:
        return None
    return s

def parse_ts(value):
    s = to_str(value)
    if s is None:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def normalize_record(raw):
    rid = to_str(raw.get("request_id"))
    warnings = []

    status = to_int(raw.get("status"))
    if status is None:
        return None, [{"request_id": rid, "warning": "unparseable status; record dropped"}]

    ts = parse_ts(raw.get("timestamp"))
    if ts is None:
        warnings.append({"request_id": rid, "warning": "missing timestamp; excluded from RPM"})

    latency = to_float(raw.get("latency_ms"))
    if latency is None:
        warnings.append({"request_id": rid, "warning": "missing latency; excluded from percentiles"})

    record = {
        "request_id": rid,
        "timestamp": ts,
        "project_id": to_str(raw.get("project_id")) or "unknown",
        "model": to_str(raw.get("model")) or "unknown",
        "status": status,
        "latency_ms": latency,
        "prompt_tokens": to_int(raw.get("prompt_tokens"), default=0),
        "completion_tokens": to_int(raw.get("completion_tokens"), default=0),
        "error_code": to_str(raw.get("error_code")),
    }
    return record, warnings

def dedupe(records):
    seen = set()
    kept, warnings = [], []
    for rec in records:
        rid = rec["request_id"]
        if rid is not None and rid in seen:
            warnings.append({"request_id": rid, "warning": "duplicate request_id; kept first"})
            continue
        if rid is not None:
            seen.add(rid)
        kept.append(rec)
    return kept, warnings