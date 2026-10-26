from pathlib import Path

from triage import build_report, load_and_clean, main

FIXTURES = Path(__file__).parent.parent / "fixtures"


def dirty_report():
    records, tiers, parse_errors, warnings = load_and_clean(
        [str(FIXTURES / "logs_dirty.jsonl")], str(FIXTURES / "tiers.csv"))
    return build_report(records, tiers, parse_errors, warnings)


def test_totals():
    totals = dirty_report()["totals"]
    assert totals == {"request_count": 10, "error_count": 3,
                      "error_rate": 0.3, "rate_limit_errors": 2}


def test_per_project_limits():
    per_project = {p["project_id"]: p for p in dirty_report()["per_project"]}
    assert per_project["proj_fin_a"]["peak_rpm"] == 3
    assert per_project["proj_fin_a"]["over_rpm_limit"] is True
    assert per_project["proj_fin_b"]["over_rpm_limit"] is False
    assert per_project["proj_unknown"]["tier"] == "unknown"
    assert per_project["proj_unknown"]["over_rpm_limit"] is None


def test_errors_and_warnings():
    report = dirty_report()
    assert len(report["parse_errors"]) == 1
    assert sorted(w["request_id"] for w in report["warnings"]) == ["req_005", "req_007", "req_008"]


def test_missing_file_exits_2():
    assert main(["-f", "no_such_file.jsonl", "--dry-run"]) == 2