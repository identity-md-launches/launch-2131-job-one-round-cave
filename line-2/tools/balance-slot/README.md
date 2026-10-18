# Balance Slot

Derive the storage key for a Solidity `mapping(address => uint256)` used for
ERC-20 balances, then optionally verify that raw word in an EIP-1186 state
witness against a state root you trust. The user supplies the token, holder,
and mapping's base slot. This handles the standard Solidity mapping formula;
it does not discover a contract's storage layout or interpret token decimals.
Python 3.9+ standard library only.

Run the real-address derivation example from the repository root:

```sh
python3 -B line-2/tools/balance-slot/balance_slot.py demo
```

This computes a candidate key using the real ZTO token and Uniswap v4
PoolManager addresses with mapping slot zero as an explicit example input. It
prints `verified: false`: no proof or claim about ZTO's layout or PoolManager's
ZTO balance is made. When tried locally, it returned the 64-byte ABI preimage
and one 32-byte candidate key. The inherited ZTO account proof shows raw slots
0 and 1 absent and does not identify ZTO's balance mapping location.

For an actual proof, first independently identify the mapping slot from reviewed
source or compiler storage-layout output, capture a witness for that derived
slot, and authenticate the state root separately. Then run:

```sh
python3 -B line-2/tools/balance-slot/balance_slot.py verify \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  --state-root 0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512 \
  --token 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --holder 0x000000000004444c5dc75cb358380d2e3de08a90 \
  --mapping-slot 0
```

That illustrative command fails closed because the inherited witness is for
slots 0 and 1, not the derived mapping key. It is not a balance check. Replace
the witness, root, and mapping slot only with caller-reviewed values. Success
proves a raw uint256 storage word at the derived key; the caller remains
responsible for the root, contract identity, mapping layout and decimals. No
network access, wallet, key, environment lookup, transaction, or dependency is
used.

Check this tool with:

```sh
python3 -B -m unittest discover -s line-2/tools/balance-slot -p 'test_*.py' -v
```
