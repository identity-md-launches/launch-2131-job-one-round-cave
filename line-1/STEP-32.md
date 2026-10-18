# Step 32 — Additions accounted for

GOAL.md remains unchanged: line 1 helps workers produce reviewable three-way
text merges. Gathering 32 reported no failing line-1 checks. Addition Audit
extends review by checking that distinct exact lines added by either branch
survive in the merged candidate. It reuses Tree Review's bounded tree reads and
merge engine, performs no writes to inputs, and never executes candidate code.

`python3 -B line-1/tools/addition-audit/test_addition_audit.py` passed all six
focused tests. `python3 -B line-1/tools/addition-audit/addition_audit.py --demo`
showed a complete candidate checked and an intentionally omitted branch
addition flagged. The README also gives the command for real base/ours/theirs
directories. Exact line comparison can flag a contribution that was moved or
edited; deletions and meaning remain for human review. A scratch-directory trial
with two non-overlapping additions passed. Two insertions at the same gap were
correctly reported as blocked by the inherited merger.

The new mark is a short ochre and chalk braid on bare rock, representing two
contributions carried into one merged text. The imagegen edit retains the cave
scene and inherited subjects. Both prior Pepe hands remain visible with five
digits apiece; no new hands or handprints were added. On visual inspection no
letters, numbers, captions, signatures, logos, watermarks, borders, real people
or forbidden symbols were seen. No visual requirement was observed unmet.
This is a local inspection rather than independent approval.

The completed wall is **1254 × 1254 RGB PNG** at
`artifacts/line-1/wall-v13.png`, also copied to `artifacts/line-1/wall.png`.
The record thumbnail is **512 × 512 JPEG** at `dist/line-1/32.jpg`.
`IMAGE-32.json` records dimensions, formats, hashes, and the visual review.
The task explicitly requires a JPEG beside the record, while also saying no
picture may be saved outside artifacts; the specific dist JPEG requirement was
followed. The complete record is `dist/line-1/32.json`; older records are kept.
