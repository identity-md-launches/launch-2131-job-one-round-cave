# Claim Bridge

Claim Bridge is a small offline handoff from line 2's verified evidence bundle
to line 3's citation workflow. It checks that every cited passage is present in
the bundle's indexed documents, that the cited document hash matches its bytes,
and that the search result marked each hit as source-verified. It does not
reverify Ethereum proofs or make a trust claim about the checkpoint; those
remain line 2's responsibility.

The tool uses only Python's standard library and never writes its inputs:

```sh
python3 -B shared/claim-bridge/bridge.py demo
```

The demo consumes the inherited real ZTO/IMD proof handoff and emits a compact
JSON bridge report. For a saved bundle:

```sh
python3 -B shared/claim-bridge/bridge.py check BUNDLE.json
```

Exit 0 means every returned citation is bound to a verified source document;
exit 1 means a citation is missing, altered, out of range, or unverified; exit
2 means the input is malformed. The result is a citation-integrity check, not a
consensus, authorship, or factual-truth claim.
