"""Summarize WS3 JSONL or emulator stdout logs; no network or cloud access."""
import argparse
import json
import math
from pathlib import Path
import sys
from uuid import UUID

FIRESTORE_KINDS = ("reads", "writes", "deletes", "aggregations")


def _percentile(values, percentile):
    return values[math.ceil(len(values) * percentile / 100) - 1]


def _firestore_counts(record):
    """Return the four per-request counters, None when absent; raise on partial or invalid."""
    fields = [f"firestore_{kind}" for kind in FIRESTORE_KINDS]
    present = [field in record for field in fields]
    if not any(present):
        return None
    counts = tuple(record.get(field) for field in fields)
    if not all(present) or any(type(count) is not int or count < 0 for count in counts):
        raise ValueError
    return counts


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
            counts = _firestore_counts(record)
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
        sample = (function, method, status, duration, counts)
        if identity in seen:
            if seen[identity] != sample:
                raise ValueError(f"Conflicting request ID at line {number}")
            continue
        seen[identity] = sample
        groups.setdefault((environment, function), []).append((duration, status, counts))

    summaries = []
    for (environment, function), samples in sorted(groups.items()):
        durations = sorted(duration for duration, _status, _counts in samples)
        count = len(samples)
        summary = {
            "environment": environment, "function": function, "requests": count,
            "client_errors": sum(400 <= status < 500 for _duration, status, _counts in samples),
            "server_errors": sum(status >= 500 for _duration, status, _counts in samples),
        }
        # Nearest-rank percentiles also work for a single request; keep the sample count visible.
        for percentile in (50, 95, 99):
            summary[f"p{percentile}_ms"] = _percentile(durations, percentile)
        summary["max_ms"] = durations[-1]
        # Records from before Firestore counting carry no counters; they are left out, not read as zero.
        counted = [counts for _duration, _status, counts in samples if counts is not None]
        if counted:
            summary["firestore_samples"] = len(counted)
            summary["firestore"] = {}
            for index, kind in enumerate(FIRESTORE_KINDS):
                values = sorted(counts[index] for counts in counted)
                summary["firestore"][kind] = {
                    "total": sum(values), "p50": _percentile(values, 50),
                    "p95": _percentile(values, 95), "max": values[-1],
                }
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
