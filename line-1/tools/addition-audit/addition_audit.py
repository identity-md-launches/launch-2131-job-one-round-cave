#!/usr/bin/env python3
"""Audit whether distinct branch-added text lines survive a three-way merge."""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TREE_PATH = Path(__file__).resolve().parents[1] / 'tree-review' / 'tree_review.py'
SPEC = importlib.util.spec_from_file_location('addition_audit_tree', TREE_PATH)
tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tree)
LIMITS = [
    'Checks exact added lines only; deletions, intent, syntax and semantics are not assessed.',
    'Repeated identical additions are required at the greatest count in either branch.',
    'A moved or edited contribution may be reported missing and needs human review.',
    'Conflicted and deleted candidates are not checked as text.',
    'Bounded stable UTF-8 trees; no atomic snapshot or path race protection.',
    'Reuses Tree Review merge logic, so shared merger defects can affect both tools.']


def added_lines(base_text, branch_text):
    """Collect exact line additions from insert/replace edits against the base."""
    base = (base_text or '').splitlines(keepends=True)
    branch = (branch_text or '').splitlines(keepends=True)
    counts = {}
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(
            a=base, b=branch, autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            for line in branch[j1:j2]:
                counts[line] = counts.get(line, 0) + 1
    return counts


def audit_candidate(path, base, ours, theirs, candidate, status='clean'):
    item = {'path': path, 'merge_status': status}
    if status.endswith('conflict'):
        item.update(status='blocked', missing=[])
        return item
    if candidate is None:
        item.update(status='deleted', missing=[])
        return item
    required = {}
    by_side = {}
    for side, text in (('ours', ours), ('theirs', theirs)):
        additions = added_lines(base, text)
        by_side[side] = additions
        for line, count in additions.items():
            required[line] = max(required.get(line, 0), count)
    present = {}
    for line in (candidate or '').splitlines(keepends=True):
        present[line] = present.get(line, 0) + 1
    missing = []
    for line, count in required.items():
        actual = present.get(line, 0)
        if actual < count:
            missing.append({'line_sha256': hashlib.sha256(line.encode('utf-8')).hexdigest(),
                            'required_occurrences': count, 'candidate_occurrences': actual,
                            'from': [side for side, additions in by_side.items()
                                     if additions.get(line, 0) > actual]})
    item.update(status='review' if missing else 'checked', missing=missing,
                candidate_sha256=hashlib.sha256(candidate.encode('utf-8')).hexdigest())
    return item


def inspect(sources):
    if len(sources) != 3:
        raise ValueError('exactly three source trees are required')
    packet = tree.combine(sources)
    entries = []
    for entry in packet['files']:
        name = entry['path']
        versions = [source['files'].get(name) for source in sources]
        entries.append(audit_candidate(name, *versions, entry['candidate'], entry['status']))
    counts = {key: sum(row['status'] == key for row in entries)
              for key in ('blocked', 'deleted', 'checked', 'review')}
    return {'schema': 'addition-audit/v1', 'passed': not (counts['blocked'] or counts['review']),
            'text_merge_clean': packet['clean'], 'inputs': packet['inputs'],
            'counts': counts, 'files': entries, 'limits': LIMITS}


def from_directories(paths):
    if len(paths) != 3:
        raise ValueError('exactly three source directories are required')
    budget = [0]
    return inspect([tree.snapshot(path, budget) for path in paths])


def demo():
    base = 'first\nlast\n'
    ours = 'first\nours contribution\nlast\n'
    theirs = 'first\ntheirs contribution\nlast\n'
    complete = 'first\nours contribution\ntheirs contribution\nlast\n'
    omitted = 'first\nours contribution\nlast\n'
    good = audit_candidate('notes.txt', base, ours, theirs, complete)
    bad = audit_candidate('notes.txt', base, ours, theirs, omitted)
    return {'complete_candidate': good, 'omitted_contribution': bad,
            'omission_detected': bad['status'] == 'review' and len(bad['missing']) == 1}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='BASE_DIR OURS_DIR THEIRS_DIR')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    if args.demo and args.paths or not args.demo and len(args.paths) != 3:
        parser.error('provide three source trees or --demo')
    try:
        report = demo() if args.demo else from_directories(args.paths)
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as error:
        print('addition-audit: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if args.demo and report['omission_detected'] or not args.demo and report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
