#!/usr/bin/env python3
"""Explain strict offline searches with cited one-term relaxations."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location(
    "diagnose_search", Path(__file__).absolute().parents[1] / "evidence-search/search.py")
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)

MAX_TERMS = 12


def diagnose(index, root, query, limit=3):
    """Run an all-terms query and each bounded query omitting one term."""
    terms = list(dict.fromkeys(search.tokens(query)))
    if not terms:
        raise search.SearchError("query must contain a word or address")
    if len(terms) > MAX_TERMS:
        raise search.SearchError(f"query has more than {MAX_TERMS} distinct terms")
    if not 1 <= limit <= 10:
        raise search.SearchError("limit must be between 1 and 10")

    strict = search.search(index, query, root, limit=limit, require_all=True)
    relaxations = []
    for omitted in terms:
        remaining = [term for term in terms if term != omitted]
        result = (search.search(index, " ".join(remaining), root, limit=limit,
                                require_all=True) if remaining else {"hits": []})
        relaxations.append({"omitted_term": omitted,
                            "query": " ".join(remaining),
                            "hit_count": len(result["hits"]),
                            "hits": result["hits"]})
    return {"format": "evidence-query-diagnosis/v1", "query": query,
            "mode": "all_terms_then_one_term_omissions",
            "indexed_documents": strict["indexed_documents"],
            "strict_hit_count": len(strict["hits"]), "strict_hits": strict["hits"],
            "relaxations": relaxations,
            "interpretation": "Omitting a term reveals lexical candidates only; it does not establish an answer or justify silently dropping the term."}


def demo():
    root = search.workspace_path(Path(__file__).absolute().parents[1]
                                 / "evidence-search/examples/docs")
    index = search.build_index(root)
    return diagnose(index, root, "ZTO pool finality", limit=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="diagnose an inherited ZTO-first query; writes nothing")
    run = commands.add_parser("run", help="diagnose a strict all-terms search in a live collection")
    run.add_argument("root")
    run.add_argument("query")
    run.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            root = search.workspace_path(args.root)
            index = search.build_index(root)
            result = diagnose(index, root, args.query, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (search.SearchError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
