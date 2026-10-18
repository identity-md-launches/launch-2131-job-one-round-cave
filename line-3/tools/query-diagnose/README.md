# Query Diagnose

Explain a strict all-terms search that returns no passages. The report runs the
original query with every distinct word required, then runs one search per word
with just that word omitted. Each candidate keeps the existing searcher's exact
line citation, source hash, ranking and live byte check. Python 3.9+ and the
standard library only; it reuses the adjacent Evidence Search engine and never
writes files or executes document content.

From the repository root, one command demonstrates the tool on inherited
historical ZTO-first documents:

```sh
python3 -B line-3/tools/query-diagnose/diagnose.py demo
```

When tried, `ZTO pool finality` had no strict all-terms result. Omitting
`finality` surfaced the exact pool reference at `pool.md:1-10`; this only shows
that the lexical constraint changed and does not establish an answer. The source
labels the pool parameters as assignment-provided, not independently verified.
The demo reads stored workspace documents, makes no network request, and writes
nothing.

For a collection in your workspace, run:

```sh
python3 -B line-3/tools/query-diagnose/diagnose.py run line-3/tools/evidence-search/examples/docs 'ZTO pool finality' --limit 2
```

Each live candidate source is re-read and checked against its indexed SHA-256.
At most 12 distinct query terms and 10 passages per query are accepted, keeping
the diagnostic bounded to one strict search and at most 12 relaxations. A
relaxation is a lead for further review: do not silently discard a missing term.
The normal Evidence Search path rules apply; collections must be local, static
UTF-8 `.md`, `.txt` or `.rst` files under the current workspace. Hashes prove
byte identity only, not factual truth or claim support.

## Checks

```sh
python3 -B line-3/tools/query-diagnose/test_diagnose.py -v
```

Four behavioral checks cover exact live citations, strict results, empty/large
query and limit rejection, and the inherited ZTO demonstration.
