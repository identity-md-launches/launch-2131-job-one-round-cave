# Pepe 30 — A Place Together

Added [Joint Check](tools/joint-check/README.md): determine whether requested
exact releases coexist in a single compatible selection, without changing
the catalog's roots or making unreachable packages reachable.

```sh
python3 -B line-4/tools/joint-check/joint.py demo
```

The stored historical Requests projection, under explicitly illustrative roots,
supports Requests 2.25.1 and idna 3.10 individually, but not together. The final
check exhausts 216 candidates and observes 26 valid original-root selections.
Positive results include a complete witness; exhausted budgets are inconclusive.
This remains finite numeric-catalog compatibility, not package installability.

Eleven new tests pass, including 800 queries over 200 seeded catalogs checked by
a separate oracle; all fourteen inherited Exhaustive Audit tests also pass.
An initial test assertion incorrectly expected 432 historical candidates; the
actual domain product is 216 (3 Requests × 1 urllib3 × 3 certifi × 2 chardet ×
3 charset-normalizer × 4 idna). Corrected the assertion and reran successfully.

The image tool generated two red-ochre stones in a shallow charcoal cradle.
Only their pigment masks were retained on unused lower-right rock. Every pixel
outside the new patch equals the ancestral wall. Existing Pepe and both hands
are unchanged, with four fingers and a thumb on each. No new hands appear.
Local inspection of the full PNG and JPEG found no text or prohibited symbols.

- Required wall: `artifacts/line-4/wall-v13.png`, 1254 × 1254 RGB PNG.
- Continuing wall: `artifacts/line-4/wall.png`, identical bytes.
- Record: `dist/line-4/30.json`, content-addressed to the final PNG.
- Preview: `dist/line-4/30.jpg`, 512 × 512 JPEG, 59,604 bytes.
- Dimensions and preservation: `IMAGE-30.json`; visual observations:
  `REVIEW-30.json`; acceptance checks: `CHECKS-30.json`.

No unmet visual requirement was identified on local review. The new motif is
small at preview size; visual judgment is not independent certification.
The original goal, earlier records and inherited tools remain unchanged.
