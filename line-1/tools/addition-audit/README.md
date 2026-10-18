# Addition Audit

Addition Audit checks whether exact lines added by either contributor remain in
the recomputed three-way merge. It flags an omitted addition for human review
without applying changes or exposing source text in the report.

Run this one command from the workspace root to see a complete candidate pass
and an intentionally omitted contribution flagged:

```sh
python3 -B line-1/tools/addition-audit/addition_audit.py --demo
```

For real, stable workspace directories:

```sh
python3 -B line-1/tools/addition-audit/addition_audit.py BASE_DIR OURS_DIR THEIRS_DIR
```

The tool uses Python's standard library and the existing bounded Tree Review
reader and merge computation. Exit 0 means no exact added line was missing and
there are no blocked candidates; exit 1 means review is needed; exit 2 means the
input could not be checked.

## Limits

It compares lines exactly. A moved, reformatted, or edited contribution can be
flagged even when its meaning survived. Deletions and semantic intent are not
evaluated. Identical additions from both branches are required once; repeated
identical additions from one branch keep their multiplicity. Conflict and
deleted candidates are reported explicitly. It reuses Tree Review's merge
logic, so it cannot independently catch a defect shared with that merger. The
bounded filesystem reader assumes stable paths and does not provide atomic
snapshots or race protection. It never executes candidate code or writes to the
input trees.

Try the focused checks with:

```sh
python3 -B line-1/tools/addition-audit/test_addition_audit.py
```

Observed: all six focused tests passed. The real-directory trial with two
non-overlapping additions passed; two insertions at the same gap were reported
as a merge conflict by the underlying Tree Review merger and correctly shown as
blocked rather than audited as a candidate.
