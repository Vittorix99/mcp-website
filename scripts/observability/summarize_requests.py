"""Summarize WS3 JSONL or emulator stdout logs; no network or cloud access."""
import argparse
import json
import math
from pathlib import Path
import sys
from uuid import UUID


def summarize_requests(lines):
    groups, seen = {}, {}
    for number, line in enumerate(lines, 1):
        text = line.strip()
        if text.startswith("> "):
            text = text[2:].lstrip()
        try:
            record = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            if "http_request_completed" in text:
                raise ValueError(f"Invalid request record at line {number}") from None
            continue
        if not isinstance(record, dict) or record.get("event") != "http_request_completed":
            continue
        try:
            environment, function = record["environment"], record["function"]
            duration, status = record["duration_ms"], record["status_code"]
            request_id = UUID(record["request_id"])
            method = record["method"]
            valid = (
                environment in {"local", "test", "staging", "production"}
                and isinstance(function, str) and function.isascii() and function.isidentifier()
                and type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
                and type(status) is int and 100 <= status <= 599
                and request_id.version == 4
                and method in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "OTHER"}
            )
        except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
            valid = False
        if not valid:
            raise ValueError(f"Invalid request record at line {number}")
        identity = (environment, str(request_id))
        sample = (function, method, status, duration)
        if identity in seen:
            if seen[identity] != sample:
                raise ValueError(f"Conflicting request ID at line {number}")
            continue
        seen[identity] = sample
        groups.setdefault((environment, function), []).append((duration, status))

    summaries = []
    for (environment, function), samples in sorted(groups.items()):
        durations = sorted(duration for duration, _status in samples)
        count = len(samples)
        summary = {
            "environment": environment, "function": function, "requests": count,
            "client_errors": sum(400 <= status < 500 for _duration, status in samples),
            "server_errors": sum(status >= 500 for _duration, status in samples),
        }
        # Nearest-rank percentiles also work for a single request; keep the sample count visible.
        for percentile in (50, 95, 99):
            summary[f"p{percentile}_ms"] = durations[math.ceil(count * percentile / 100) - 1]
        summary["max_ms"] = durations[-1]
        summaries.append(summary)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", nargs="?", default="-", help="Log file, or - for stdin")
    args = parser.parse_args()
    try:
        if args.log == "-":
            summaries = summarize_requests(sys.stdin)
        else:
            with Path(args.log).open(encoding="utf-8") as source:
                summaries = summarize_requests(source)
        if not summaries:
            raise ValueError("No request records found")
    except (OSError, UnicodeError):
        print("Cannot read request log", file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(summaries, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
