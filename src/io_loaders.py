import json


def load_jsonl(path):
    records, errors = [], []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append({"file": path, "line": lineno, "error": str(exc)})
                continue
            if not isinstance(obj, dict):
                errors.append({"file": path, "line": lineno, "error": "not a JSON object"})
                continue
            records.append(obj)
    return records, errors