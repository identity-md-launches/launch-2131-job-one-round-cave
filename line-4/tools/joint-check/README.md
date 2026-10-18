# Joint Check

Check whether several exact releases can occur **together in one complete,
compatible selection reachable from the original roots**. This catches a trap
that individual release viability cannot: two releases may each work in some
selection but never work together. Pins require presence; they do not turn an
unreachable package into a new root.

From the repository root, run this offline, standard-library Python command:

```sh
python3 -B line-4/tools/joint-check/joint.py demo
```

The demo reuses the stored historical Requests metadata projection from
`../conflict-core/examples/requests-conflict.json`, with **explicit illustrative
roots** `requests: *` and `urllib3: <2`, replacing that file's conflict roots
in memory. It observes Requests 2.25.1 and idna 3.10 as individually compatible,
with full witnesses, then exhausts 216 candidates to show they cannot coexist:
that Requests release requires idna below 3. This is a historical finite
projection, not a statement about installed packages or current PyPI.

Check your own workspace-local catalog using the inherited Offline Resolver
`packages`/`roots` JSON format:

```sh
python3 -B line-4/tools/joint-check/joint.py path/to/catalog.json --require app=1.0 --require dep=2
```

For another historical trial, add the same `--require` arguments to `demo`.
This retains the demo's explicitly illustrative roots. Without `--require`,
`demo` runs the three checks above. Package aliases normalize to lowercase
hyphens; equivalent numeric spellings (1 versus 1.0) use the catalog label.
Duplicate canonical pins are rejected. Exact catalog labels and normalized
pins appear in each report, along with a SHA-256 of normalized catalog data.

Exit codes: 0 compatible (or the expected three-result demo), 1 incompatible,
2 invalid input/read error, 3 inconclusive. `--max-assignments N` accepts
1 through 1,000,000 (default 10,000). A complete witness suffices for a positive
claim; a negative claim requires exhausting the original candidate domain.
Budget exhaustion never claims incompatibility. The special multi-check demo
returns 3 if its expected outcomes are not established.

The catalog loader rejects paths resolving outside the current workspace,
duplicate JSON keys, and inputs over 1 MB. No discovery, environment access,
package execution, network, installation, wallet or transaction is performed.
The tool imports the sibling Exhaustive Audit edge/reachability checker and
Offline Resolver's grammar/loader. Keep these sibling folders when copying it.
It never calls the original resolver search or its compatibility predicate.

Validation command:

```sh
python3 -B -m unittest discover -s line-4/tools/joint-check -p 'test_*.py' -v
```

Eleven tests cover mutually exclusive viable choices, branch-dependent presence,
cycles, unreachable/missing packages, empty domains, exact budget boundaries,
aliases, input preservation, CLI statuses and the historical example. A separate
test oracle checks 800 pin queries over 200 seeded catalogs. These are local
observations; they do not certify arbitrary catalog data.

Limits: enumeration grows exponentially. The inherited grammar supports only
finite numeric versions and conjunctive constraints. Markers, extras, platform
compatibility, artifact availability and publisher trust are not modeled. An
incompatible query can also mean the original roots themselves are impossible;
the report's `compatible_selections_seen` distinguishes whether any valid
original-root selection was observed. No minimal conflicting pin set is claimed.
