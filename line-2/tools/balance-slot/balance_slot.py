#!/usr/bin/env python3
"""Derive and verify a Solidity ERC-20 balance mapping storage key."""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFIER = HERE.parent / 'state-witness' / 'witness.py'
spec = importlib.util.spec_from_file_location('balance_slot_state_witness', VERIFIER)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

ZTO = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
POOL_MANAGER = '0x000000000004444c5dc75cb358380d2e3de08a90'


def derive(token, holder, mapping_slot):
    """Return keccak256(abi.encode(holder, mapping_slot)) for a mapping."""
    token_bytes = w.hex_data(token, 20, 'token address')
    holder_bytes = w.hex_data(holder, 20, 'holder address')
    w.require(type(mapping_slot) is int and 0 <= mapping_slot < 1 << 256,
              'mapping slot must be a uint256')
    preimage = holder_bytes.rjust(32, b'\0') + mapping_slot.to_bytes(32, 'big')
    key = w.keccak256(preimage)
    return {
        'format': 'erc20-balance-slot/1',
        'token': w.hex0(token_bytes),
        'holder': w.hex0(holder_bytes),
        'mappingSlot': hex(mapping_slot),
        'preimage': w.hex0(preimage),
        'storageSlot': w.hex0(key),
        'formula': 'keccak256(leftPad32(holder) || uint256(mappingSlot))',
        'assumption': 'The caller must independently confirm that this token stores balances at the supplied Solidity mapping slot.',
    }


def verify_bundle(bundle, token, holder, mapping_slot, state_root):
    result = derive(token, holder, mapping_slot)
    proof = bundle.get('proof') if isinstance(bundle, dict) else None
    state = w.verify(proof, state_root, result['token'], [result['storageSlot']])
    value = next(row['value'] for row in state['storage']
                 if int(row['slot'], 16) == int(result['storageSlot'], 16))
    result.update({
        'verified': True,
        'stateRoot': state['stateRoot'],
        'rawStorageValue': value,
        'rawStorageValueDecimal': str(int(value, 16)),
        'meaning': 'A raw uint256 value proven at the derived slot; decimals and token storage layout are caller assumptions.',
        'trust': 'Proof is relative to the supplied state root. Authenticate that root and independently review the mapping slot and token implementation.',
    })
    return result


def parse_mapping_slot(value):
    if not isinstance(value, str) or re.fullmatch(r'(?:0x[0-9a-fA-F]{1,64}|[0-9]+)', value) is None:
        raise argparse.ArgumentTypeError('mapping slot must be decimal or 0x-prefixed uint256')
    number = int(value, 16) if value.startswith('0x') else int(value, 10)
    if number >= 1 << 256:
        raise argparse.ArgumentTypeError('mapping slot exceeds uint256')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='derive a candidate key using real ZTO and PoolManager addresses')
    demo.set_defaults(token=ZTO, holder=POOL_MANAGER, mapping_slot=0)
    derive_cli = sub.add_parser('derive', help='derive a candidate balance mapping key')
    derive_cli.add_argument('--token', required=True)
    derive_cli.add_argument('--holder', required=True)
    derive_cli.add_argument('--mapping-slot', required=True, type=parse_mapping_slot)
    check = sub.add_parser('verify', help='verify the derived raw storage word against a trusted state root')
    check.add_argument('bundle', help='state-witness/1 JSON inside the current workspace')
    check.add_argument('--state-root', required=True)
    check.add_argument('--token', required=True)
    check.add_argument('--holder', required=True)
    check.add_argument('--mapping-slot', required=True, type=parse_mapping_slot)
    args = parser.parse_args(argv)
    try:
        if args.command == 'verify':
            bundle = w.load_bundle(args.bundle)
            result = verify_bundle(bundle, args.token, args.holder,
                                   args.mapping_slot, args.state_root)
        else:
            result = derive(args.token, args.holder, args.mapping_slot)
            result['verified'] = False
            result['note'] = 'Derivation only; no proof, storage layout or token balance was checked.'
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, StopIteration):
        print(json.dumps({'verified': False, 'error': 'Malformed input or proof.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
