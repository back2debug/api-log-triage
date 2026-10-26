import argparse, json, sys
from dataclasses import dataclass, asdict
from api_client import run_triage_agent

@dataclass
class Config:
    prompt: str | None
    files: list[str]
    tiers: str | None
    model: str
    timeout: float
    dry_run: bool
    pretty: bool
    quiet: bool

def parse_args(argv=None) -> Config:
    p = argparse.ArgumentParser(description="Enterprise API incident triage")
    p.add_argument("prompt", nargs="?", help="free-text prompt")
    p.add_argument("-f", "--file", action="append", default=[], help="log file (repeatable)")
    p.add_argument("-c", "--tiers", help="tier config CSV")
    p.add_argument("-m", "--model", default="gpt-4o-mini")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--dry-run", action="store_true", help="skip the API call")
    p.add_argument("--pretty", action="store_true", help="indent JSON output")
    p.add_argument("--quiet", action="store_true", help="suppress extra output")
    ns = p.parse_args(argv)
    return Config(ns.prompt, ns.file, ns.tiers, ns.model,ns.timeout, ns.dry_run, ns.pretty, ns.quiet)

def main(argv=None) -> int:
    cfg = parse_args(argv)
    result = {"status": "ok", "config": asdict(cfg)}
    print(json.dumps(result, indent=2 if cfg.pretty else None))
    return 0

if __name__ == "__main__":
    sys.exit(main())