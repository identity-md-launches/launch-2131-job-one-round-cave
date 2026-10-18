#!/usr/bin/env python3
"""Bind line 3 citations to the exact documents emitted by line 2."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent / "proof-handoff" / "examples" / "zto-proof-bundle.json"
MAX_BYTES = 2 * 1024 * 1024


def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("bundle exceeds 2 MiB")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("bundle must be an object")
    return value


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bridge(bundle):
    index = bundle.get("index")
    receipt = bundle.get("receipt")
    if not isinstance(index, dict) or not isinstance(receipt, dict):
        raise ValueError("missing index or receipt")
    docs = index.get("documents")
    result = receipt.get("result")
    if not isinstance(docs, list) or not isinstance(result, dict):
        raise ValueError("malformed index or receipt result")

    by_path = {}
    for doc in docs:
        if not isinstance(doc, dict) or not isinstance(doc.get("path"), str):
            raise ValueError("malformed indexed document")
        path = doc["path"]
        text = doc.get("text")
        digest = doc.get("sha256")
        if not isinstance(text, str) or not isinstance(digest, str):
            raise ValueError("document lacks text or sha256")
        if sha256(text) != digest:
            raise ValueError("indexed document hash mismatch")
        if path in by_path:
            raise ValueError("duplicate document path")
        by_path[path] = (text, digest)

    hits = result.get("hits")
    if not isinstance(hits, list):
        raise ValueError("receipt has no hits")
    checked = []
    failures = []
    for hit in hits:
        if not isinstance(hit, dict):
            failures.append("malformed hit")
            continue
        path = hit.get("path")
        start = hit.get("line_start")
        end = hit.get("line_end")
        digest = hit.get("sha256")
        text = by_path.get(path, (None, None))[0]
        reason = None
        if text is None:
            reason = "citation path is not indexed"
        elif not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            reason = "invalid citation range"
        elif end > len(text.splitlines()):
            reason = "citation range exceeds source"
        elif digest != by_path[path][1]:
            reason = "citation hash differs from source"
        elif hit.get("source_verified") is not True:
            reason = "citation is not source-verified"
        entry = {"path": path, "line_start": start, "line_end": end}
        if reason:
            entry["error"] = reason
            failures.append(reason)
        else:
            entry["verified"] = True
        checked.append(entry)
    return {
        "format": "claim-bridge/v1",
        "documents": len(by_path),
        "citations": len(hits),
        "verified": not failures,
        "checked": checked,
        "failures": failures,
        "trust": "Citation integrity only; proof checkpoint trust remains external.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    check = sub.add_parser("check")
    check.add_argument("bundle")
    args = parser.parse_args(argv)
    try:
        value = bridge(load(DEMO if args.command == "demo" else args.bundle))
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0 if value["verified"] else 1
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"format": "claim-bridge/v1", "verified": False,
                          "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
