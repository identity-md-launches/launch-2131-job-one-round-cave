# Round 33 — The Balance Root

Balance Slot derives the Solidity storage key for a standard ERC-20 balance mapping from an explicitly supplied holder address and mapping base slot. Its `verify` command checks that raw word against a caller-supplied state root using the inherited State Witness verifier. The layout slot must come from independently reviewed contract storage information; this tool does not discover it or assign token decimals.

Run the real-address derivation example offline:

```sh
python3 -B line-2/tools/balance-slot/balance_slot.py demo
```

It computes a candidate key for ZTO and the real Uniswap v4 PoolManager using mapping slot zero, and explicitly reports `verified: false`. It makes no ZTO balance claim. Three unit tests passed. The helper and limits are documented in `tools/balance-slot/README.md`.

The wall remains a 1254 × 1254 RGB PNG. The new ochre and charcoal branch glyph sits on previously unpainted upper-right rock. Local comparison confirms zero changed pixels outside its small feathered patch. The heavy-lidded wide-mouthed Pepe remains visible; each visible hand has five digits. No text or other unmet visual requirement was observed. Review and format measurements are in `REVIEW-33.json`.
