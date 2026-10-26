import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass

from api_client import DEFAULT_MODEL, run_triage_agent
from io_loaders import load_jsonl, load_tiers
from metrics import group_stats, is_success, over_limit, peak_per_minute, safe_div
from normalize import dedupe, normalize_record, normalize_tier

ASSUMPTIONS = [
    "success = 200 <= status < 300",
    "latency percentiles use successful requests only (linear interpolation)",
    "peak RPM/TPM = busiest calendar minute in UTC",
    "tokens = prompt + completion, missing counted as 0, all requests",
    "duplicate request_id: first occurrence kept",
    "records without a timestamp count in totals but not in RPM/TPM",
    "unknown project: tier 'unknown', limits null, over_limit null",
]


@dataclass
class Config:
    files: list[str]
    tiers: str | None
    model: str
    dry_run: bool
    pretty: bool


def parse_args(argv=None) -> Config:
    p = argparse.ArgumentParser(description="Enterprise API incident triage")
    p.add_argument("-f", "--file", action="append", required=True, help="JSONL log file (repeatable)")
    p.add_argument("-c", "--tiers", help="tier config CSV")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL)
    p.add_argument("--dry-run", action="store_true", help="skip the API call")
    p.add_argument("--pretty", action="store_true", help="indent JSON output")
    ns = p.parse_args(argv)
    return Config(ns.file, ns.tiers, ns.model, ns.dry_run, ns.pretty)


def load_and_clean(files, tiers_path):
    raw, parse_errors, warnings = [], [], []
    for path in files:
        recs, errs = load_jsonl(path)
        raw.extend(recs)
        parse_errors.extend(errs)

    cleaned = []
    for r in raw:
        rec, w = normalize_record(r)
        warnings.extend(w)
        if rec is not None:
            cleaned.append(rec)
    records, dup_warnings = dedupe(cleaned)
    warnings.extend(dup_warnings)

    tiers = {}
    if tiers_path:
        raw_tiers, tier_errors = load_tiers(tiers_path)
        parse_errors.extend(tier_errors)
        tiers = {pid: normalize_tier(row) for pid, row in raw_tiers.items()}
    return records, tiers, parse_errors, warnings


def build_report(records, tiers, parse_errors, warnings):
    by_project_model = defaultdict(list)
    by_project = defaultdict(list)
    for r in records:
        by_project_model[(r["project_id"], r["model"])].append(r)
        by_project[r["project_id"]].append(r)

    per_project_model = [
        {"project_id": project, "model": model, **group_stats(group)}
        for (project, model), group in sorted(by_project_model.items())
    ]

    unknown_tier = {"tier": "unknown", "rpm_limit": None, "tpm_limit": None}
    per_project = []
    for project, group in sorted(by_project.items()):
        tier = tiers.get(project, unknown_tier)
        peak_rpm = peak_per_minute((r["timestamp"], 1) for r in group)
        peak_tpm = peak_per_minute(
            (r["timestamp"], r["prompt_tokens"] + r["completion_tokens"]) for r in group)
        per_project.append({
            "project_id": project,
            "tier": tier["tier"],
            "peak_rpm": peak_rpm,
            "rpm_limit": tier["rpm_limit"],
            "over_rpm_limit": over_limit(peak_rpm, tier["rpm_limit"]),
            "peak_tpm": peak_tpm,
            "tpm_limit": tier["tpm_limit"],
            "over_tpm_limit": over_limit(peak_tpm, tier["tpm_limit"]),
        })

    error_count = sum(1 for r in records if not is_success(r["status"]))
    return {
        "assumptions": ASSUMPTIONS,
        "totals": {
            "request_count": len(records),
            "error_count": error_count,
            "error_rate": safe_div(error_count, len(records)),
            "rate_limit_errors": sum(1 for r in records if r["status"] == 429),
        },
        "per_project_model": per_project_model,
        "per_project": per_project,
        "parse_errors": parse_errors,
        "warnings": warnings,
    }


def main(argv=None) -> int:
    cfg = parse_args(argv)
    try:
        records, tiers, parse_errors, warnings = load_and_clean(cfg.files, cfg.tiers)
    except OSError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 2

    report = build_report(records, tiers, parse_errors, warnings)

    if cfg.dry_run:
        report["customer_summary"] = {"skipped": "dry run"}
    else:
        agent_input = json.dumps({k: report[k] for k in ("totals", "per_project_model", "per_project")})
        report["customer_summary"] = run_triage_agent(agent_input, model=cfg.model)

    print(json.dumps(report, indent=2 if cfg.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())