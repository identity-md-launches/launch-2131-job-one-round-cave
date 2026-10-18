#!/usr/bin/env python3
"""Check whether exact release choices coexist in a reachable finite selection."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

CHECKER = Path(__file__).resolve().parent.parent / 'exhaustive-audit/audit.py'
if not CHECKER.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('joint_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
fmt = checker.fmt


def joint_check(data, pins, max_assignments=10000):
    """Pins require presence, but never introduce new roots or dependencies."""
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise fmt.Invalid('max_assignments must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    if not isinstance(pins, dict) or not pins or len(pins) > 1000:
        raise fmt.Invalid('pins must be a nonempty object of at most 1000 releases')
    normalized = {}
    for raw, release in pins.items():
        package = fmt.name(raw)
        if package in normalized:
            raise fmt.Invalid('duplicate canonical pin: ' + package)
        numeric = fmt.version(release)
        # Equivalent numeric spellings select the catalog's original label.
        normalized[package] = next((v for v in packages.get(package, {})
                                    if fmt.version(v) == numeric), release)
    pins = dict(sorted(normalized.items()))
    payload = {'packages': packages, 'roots': roots}
    base = {'method': 'finite-joint-check-v1', 'pins': pins,
            'catalog_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(),
            'max_assignments': max_assignments}
    possible, todo = set(), list(roots)
    while todo:
        package = todo.pop()
        if package in possible:
            continue
        possible.add(package)
        for deps in packages.get(package, {}).values():
            todo.extend(deps)
    names = sorted(possible)
    domains, total = [], 1
    for p in names:
        versions = sorted(packages.get(p, {}), key=fmt.version)
        domain = ([v for v in versions if checker.matches(v, roots[p])]
                  if p in roots else [None] + versions)
        domains.append(domain)
        total *= len(domain)
    base['candidate_assignments'] = total
    checked, compatible = 0, 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            return dict(base, status='inconclusive', checked_assignments=checked,
                        compatible_selections_seen=compatible,
                        reason='budget exhausted; no joint impossibility claim')
        checked += 1
        selected = {p: v for p, v in zip(names, values) if v is not None}
        reached = checker.assignment(packages, roots, selected)
        if reached is None or reached != selected:
            continue
        compatible += 1
        if all(reached.get(p) == v for p, v in pins.items()):
            return dict(base, status='compatible', checked_assignments=checked,
                        compatible_selections_seen=compatible, witness=reached)
    return dict(base, status='incompatible', checked_assignments=checked,
                compatible_selections_seen=compatible,
                reason='all original-root reachable selections exhausted without all pins')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace-local catalog JSON, or demo')
    parser.add_argument('--require', action='append', default=[], metavar='PACKAGE=VERSION')
    parser.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        pins = {}
        for text in args.require:
            if text.count('=') != 1:
                raise fmt.Invalid('each --require must be PACKAGE=VERSION')
            raw, release = text.split('=')
            package = fmt.name(raw)
            if package in pins:
                raise fmt.Invalid('duplicate canonical pin: ' + package)
            pins[package] = release
        path = CHECKER.parent.parent / 'conflict-core/examples/requests-conflict.json' if args.catalog == 'demo' else args.catalog
        data = fmt.load(path)
        if args.catalog == 'demo':
            # Explicit hypothetical roots over the unchanged historical releases.
            data = dict(data, roots={'requests': '*', 'urllib3': '<2'})
        if args.catalog == 'demo' and not pins:
            # Both releases are individually viable in the historical projection.
            # Requests 2.25.1 nevertheless requires idna <3.
            result = {'demonstration': 'individual viability does not imply joint viability',
                      'demonstration_roots': data['roots'],
                      'checks': [joint_check(data, p, args.max_assignments) for p in
                                 ({'requests': '2.25.1'}, {'idna': '3.10'},
                                  {'requests': '2.25.1', 'idna': '3.10'})]}
            expected = ['compatible', 'compatible', 'incompatible']
            code = 0 if [r['status'] for r in result['checks']] == expected else 3
        else:
            result = joint_check(data, pins, args.max_assignments)
            code = {'compatible': 0, 'incompatible': 1, 'inconclusive': 3}[result['status']]
    except (fmt.Invalid, OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
