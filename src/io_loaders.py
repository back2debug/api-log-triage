import json
import csv


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

def load_tiers(path):
    tiers, errors = {}, []
    with open(path, encoding="utf-8", newline="") as fh:
        for lineno, row in enumerate(csv.DictReader(fh), start=2):
            project_id = (row.get("project_id") or "").strip()
            if not project_id:
                errors.append({"file": str(path), "line": lineno, "error": "missing project_id"})
                continue
            tiers[project_id] = row
    return tiers, errors