# api-log-triage

A command-line tool that turns API request logs into an incident triage report.

Give it a JSONL export of request logs and, optionally, a CSV of rate-limit tiers. It produces a JSON report with error rates, latency percentiles, token usage, and each project's busiest minute compared against its rate limits. It can also ask an OpenAI model for a short customer-facing summary of what went wrong.

It is built for the first hour of an incident like "elevated latency and intermittent 429s since 14:00": what happened, which project, and whether it hit its limits.

## Features

- **Per project and model:** request, success and error counts, error rate, p50/p95/p99 latency, total tokens, and 429 count
- **Per project:** peak requests per minute (RPM) and tokens per minute (TPM), compared against tier limits
- **Handles messy data:** malformed lines, numbers stored as strings, blank values, missing timestamps, and duplicate request IDs are recorded as errors or warnings instead of stopping the run
- **Optional AI summary:** symptoms, likely cause, and a recommended next action, returned in a fixed structure via the OpenAI Agents SDK
- **Offline mode:** `--dry-run` skips the API entirely

## Requirements

- Python 3.10 or newer
- An OpenAI API key, only if you want the AI summary

## Installation

```bash
git clone https://github.com/back2debug/api-log-triage.git
cd api-log-triage
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the AI summary, set your key in the environment:

```bash
export OPENAI_API_KEY="your-key-here"
```

## Usage

```bash
python src/triage.py -f fixtures/logs_dirty.jsonl -c fixtures/tiers.csv --pretty
```

| Flag | Description |
| --- | --- |
| `-f`, `--file` | JSONL log file. Required; repeat it to combine several files. |
| `-c`, `--tiers` | CSV of rate-limit tiers. Without it, every project's limits are unknown. |
| `-m`, `--model` | Model for the summary. Defaults to `$OPENAI_MODEL`, or `gpt-4o-mini`. |
| `--dry-run` | Skip the API call. Everything else still runs. |
| `--pretty` | Indent the JSON output. |

The report is printed to stdout, so you can save or pipe it:

```bash
python src/triage.py -f logs.jsonl -c tiers.csv --dry-run > report.json
```

## Input formats

**Logs (JSONL),** one request per line:

```json
{"request_id":"req_001","timestamp":"2026-10-19T14:00:05Z","project_id":"proj_fin_a","model":"gpt-4o","status":200,"latency_ms":812,"prompt_tokens":1204,"completion_tokens":318,"error_code":null}
```

**Tiers (CSV):**

```csv
project_id,tier,rpm_limit,tpm_limit
proj_fin_a,tier_1,2,40000
```

## Example output

Trimmed to one project:

```json
{
  "totals": {
    "request_count": 10,
    "error_count": 3,
    "error_rate": 0.3,
    "rate_limit_errors": 2
  },
  "per_project": [
    {
      "project_id": "proj_fin_a",
      "tier": "tier_1",
      "peak_rpm": 3,
      "rpm_limit": 2,
      "over_rpm_limit": true,
      "peak_tpm": 2740,
      "tpm_limit": 40000,
      "over_tpm_limit": false
    }
  ],
  "warnings": [
    {"request_id": "req_008", "warning": "duplicate request_id; kept first"}
  ],
  "customer_summary": {"skipped": "dry run"}
}
```

The full report also includes per project-and-model statistics, parse errors, and the list of assumptions used.

## How the numbers are calculated

Every report lists its rules under `assumptions`. Two worth knowing up front: latency percentiles use successful requests only (a 429 that returns in 40 ms would make latency look better than it is), and projects missing from the tiers file get `null` limits rather than `false`, since there's nothing to compare against.

## Sample data

`fixtures/` contains small, made-up datasets. `logs_dirty.jsonl` deliberately includes a malformed line, string-typed numbers, a missing latency, a missing timestamp, an unknown project, and a duplicate ID. The limits in `tiers.csv` are scaled down to fit the small sample, so the over-limit check has something to detect.

## Project layout

```text
src/
  triage.py       CLI entry point: parses arguments, builds and prints the report
  io_loaders.py   Reads JSONL and CSV files
  normalize.py    Cleans values and records, removes duplicates
  metrics.py      Pure calculations: rates, percentiles, per-minute peaks
  api_client.py   All OpenAI API calls (Responses API and Agents SDK)
  smoke.py        Quick check that your API key and connection work
  agent_hello.py  Minimal Agents SDK example, useful for checking the SDK works on its own
fixtures/         Sample data
```

Only `api_client.py` makes network calls, so everything else can be tested offline.

## Running the tests

```bash
python -m pytest -q
```

The tests use the sample data and a fake API client, so they need no API key and make no network calls.