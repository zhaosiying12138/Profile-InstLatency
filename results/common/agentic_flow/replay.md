# Humanize2 Replay Notes

Status: Round 11 current-head capture package after commit `8ec7a8a8`. This
is intentionally not a completion claim: the real-platform gate still lacks
explicit machine-readable human approval or stronger evidence for 9 unresolved
`non_identifiable` rows.

## Checkout

Use the profiling checkout:

```bash
cd /home/zhaosiying/codebase/compiler/profile_inst_latency
```

The read-only LLVM source checkout referenced by the plan is:

```bash
/home/zhaosiying/codebase/compiler/llvm-project-21
```

The gated LLVM implementation evidence is recorded in:

```text
results/common/llvm_yushuxin_implementation.md
```

## RLCR State

The persistent RLCR prompt, review, and summary files are under:

```text
.humanize/rlcr/2026-05-23_01-15-03/
```

Important files for replay:

- `round-2-summary.md` and `round-2-review-result.md`: shared real-platform
  candidate search was introduced, but review kept AC-9/AC-16 blocked by
  non-chainable T11 latency evidence, skipped T20 resource checks, conflicts,
  and missing approval.
- `round-3-summary.md` and `round-3-review-result.md`: generated and ran the
  expanded real T20 diagnostics, reached 7190 checked-in `results/r01` and
  `results/r02` trace files, and converted the remaining conflicts into
  conservative `non_identifiable` rows; review kept T20 and T12 simulator gaps
  open.
- `round-4-summary.md` and `round-4-review-result.md`: added subject-side T20
  pair checks and T12 clean-prefix constraints, regenerated real-platform
  artifacts, and reopened AC-12/AC-13 because this capture tree was stale.
- `round-5-prompt.md`: Round 5 boundary. It identifies the Round 4 blockers:
  peer-side T20 constraints, T12 short-sweep exactness guard, stale
  Humanize2/agentic-flow capture, and missing explicit approval.
- `round-5-summary.md`: records candidate-simulator Worker Anscombe at commit
  `773f27d6` and capture Worker Kepler at commit `cfd9a788`.
- `round-5-review-result.md`: accepts the candidate-simulator fixes from
  `773f27d6`, finds the Round 5 code-worker capture package missing, and keeps
  AC-16 blocked by absent explicit approval and unresolved risk handling.
- `round-6-summary.md`: records Round 5 code-worker capture backfill at commit
  `7a76e62f` and approval-gate Worker Gibbs at commit `ea7c0aca`.
- `round-6-review-result.md`: accepts the Round 6 approval-gate behavior,
  finds the Gibbs capture package missing, updates the current hashes, and
  keeps AC-16 blocked by absent explicit approval plus 39 unresolved
  `non_identifiable` risks.
- `round-8-summary.md`: records the blocked human handoff state. No approval
  artifact was created.
- `round-8-review-result.md`: keeps AC-16 blocked and identifies that the
  pre-Round-9 field-status sidecar undercounted approval-bound
  `non_identifiable` rows in `blocking_total`.
- `round-9-prompt.md`: dispatches the fix for the field-status summary
  undercount and requires refreshed request hashes and Humanize2 capture.
- `round-9-summary.md`: records the Round 9 code-worker result.
- `round-10-prompt.md`: dispatches stronger T20/T12 evidence work and asks the
  capture worker to update Humanize2 state and write this Round 10 summary.
- `round-10-summary.md`: records the focused evidence refresh and keeps the
  real-platform gate fail-closed.
- `round-10-review-result.md`: current-head review found stale Humanize2
  capture and search reproduction drift; commit `8ec7a8a8` fixed the search
  reproduction path while leaving AC-16 fail-closed.

Do not edit `.humanize/rlcr/**` from worker tasks. This replay records where
those files are read, not a modification of RLCR state.

## Modes

- `synthetic_calibration`: use configured cmodel ground truth to repair
  templates, prompts, schemas, inference, and mismatch reporting.
- `real_platform_profile`: do not use golden equality. Stop on coverage,
  stability, confidence, assumptions, conflict resolution, and explicit human
  approval.

## Evidence Snapshot

Round 4 summary hashes, preserved as the review baseline:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `5371f4c4c8dd8c7c292b6143243f1d9e5c68fdcbf70d2fa75274afe58885f9f4` |
| `results/common/real_platform_field_status.json` | `a629c52497ca8eade0e197d6e8e398558f1c89ea13d85823d21a1b443f21a4a8` |
| `results/common/search_model_real_platform.json` | `ed813bcec76b943e36134efcbedbe87866a1f5f73aba40206be211ebec24f935` |
| `results/common/experiment_quality.md` | `8206055ea8ab05c8864203890332cb9d742d3508430c986dca7b78e5df19b9b8` |

Current Round 11 approval-bound hashes after current-head capture:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `197787ab2389df7a059aa9221a70dc5c03c4a18f7dade0c605aca939faa671fd` |
| `results/common/real_platform_field_status.json` | `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432` |
| `results/common/search_model_real_platform.json` | `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6` |
| `results/common/experiment_quality.md` | `d3c2e41f9bcd1a3b92ed2e148be5929d82a8ae111486c7471755030f7af1a31a` |

Current source-backed counts:

- `results/common/experiment_quality.md` reports 7660 real-platform traces,
  178/178 required real gem5 groups, 3815 stable repeat groups, and 0 unstable
  repeat groups.
- `results/common/real_platform_field_status.json` has 150 rows: 141
  `inferred`, 9 `non_identifiable`, 0 `conflict`, and 0
  `insufficient_evidence`.
- `results/common/real_platform_field_status.json` now reports
  `summary.blocking_total = 9` and
  `summary.blocking_status_counts.non_identifiable = 9`.
- `results/common/experiment_quality.md` reports `Gate status: NOT_READY`,
  `Confidence: unresolved_llvm_field_status`, and `Human approval status:
  absent`.
- `find results/common -maxdepth 1 -iname '*approval*' -print` is empty.
- `results/common/real_platform_risk_acceptance_request.json` is a pending
  request artifact. It is not consumed by the gate and is not a human approval
  artifact.

## Round 5 Code Worker Capture Package

Worker Anscombe's original prompt transcript was not checked in. The replay
therefore uses normalized reconstructed artifacts, explicitly labeled as such:

- Prompt: `artifacts/prompts/round-5-code-worker-candidate-simulator.md`
- Contract: `artifacts/worker_contracts/worker-r5-code.md`
- Output: `artifacts/worker_outputs/worker-r5-code.md`
- Verification: `artifacts/verification/worker-r5-code.md`
- Tool calls: `artifacts/tool_calls/worker-r5-code-normalized.json`

Allowed write scope reconstructed from commit `773f27d6`:

- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`

Success criteria reconstructed from Round 5 review:

- Peer-side T20 observations constrain rows that only appear as
  `pair_instruction_id`.
- `vredsum_vs` receives peer-side T20 groups in the regenerated real-platform
  search artifact.
- T12 clean-prefix exact latency requires trailing no-stall residual plateau
  coverage.
- Short K0/K1 T12 sweeps remain `non_identifiable`.
- Unit tests and review regeneration checks pass.
- Synthetic gate passes.
- Real-platform gate fails closed until explicit approval exists.

State-changing commands captured for replay:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results
```

Verification commands captured for replay:

```bash
python3 -m unittest tests.test_search_model_candidate_sim
python3 -m pytest -q
python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py
python3 -m json.tool results/common/search_model_real_platform.json >/dev/null
python3 -m json.tool results/common/real_platform_field_status.json >/dev/null
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
find results/common -maxdepth 1 -iname '*approval*' -print
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
git diff --check
```

At the Round 5 boundary, the real-platform gate command was expected to return
nonzero until a machine-readable human approval artifact existed, covered the
39 unresolved field-status risks, bound the then-current inventory and
field-status hashes, and the quality report said `Gate status: PASS`.

## Round 6 Approval-Gate Capture Package

Worker Gibbs' exact prompt transcript was not checked in. The replay therefore
uses normalized reconstructed artifacts, explicitly labeled as such:

- Prompt: `artifacts/prompts/round-6-approval-gate-worker-gibbs.md`
- Contract: `artifacts/worker_contracts/worker-r6-gibbs-approval-gate.md`
- Output: `artifacts/worker_outputs/worker-r6-gibbs-approval-gate.md`
- Verification: `artifacts/verification/worker-r6-gibbs-approval-gate.md`
- Tool calls:
  `artifacts/tool_calls/worker-r6-gibbs-approval-gate-normalized.json`

Allowed write scope reconstructed from commit `ea7c0aca`:

- `scripts/analyze.py`
- `scripts/check_calibration_gate.py`
- `tests/test_check_calibration_gate_approval.py`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`

Success criteria reconstructed from Round 6 review:

- `non_identifiable` field-status rows are blocking unresolved risks.
- Approval must record current `inventory_sha256`.
- Approval must record current `real_platform_field_status_sha256`.
- Approval must cover the unresolved field-status risk scope by accepted risk
  IDs or all-risk acceptance.
- Unit tests and review checks pass.
- Synthetic gate passes.
- Real-platform gate fails closed on missing `Gate status: PASS`, missing
  approval, and 39 unresolved `non_identifiable` risks.

Verification commands captured for replay:

```bash
python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval
python3 -m pytest -q
python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r6-approval-search.json --format json
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 -m json.tool /tmp/profile-inst-latency-r6-approval-search.json >/dev/null
find results/common -maxdepth 1 -iname '*approval*' -print
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
git diff --check
```

## Round 7 Risk-Acceptance Request Package

The Round 7 request-worker is a normalized self-capture:

- Request:
  `../real_platform_risk_acceptance_request.json`
- Prompt: `artifacts/prompts/round-7-risk-acceptance-request-worker.md`
- Contract: `artifacts/worker_contracts/worker-r7-risk-request.md`
- Output: `artifacts/worker_outputs/worker-r7-risk-request.md`
- Verification: `artifacts/verification/worker-r7-risk-request.md`
- Tool calls: `artifacts/tool_calls/worker-r7-risk-request.json`

Allowed write scope:

- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/agentic_flow/**`

Forbidden write scope:

- `.humanize/**`
- scripts
- tests
- existing generated real-platform outputs
- any new file under `results/common` whose name contains `approval`

At the Round 7 boundary, the request was bound to the then-current Round 6
hashes. The active request metadata has since been superseded by the Round 10
focused-evidence refresh below:

- Inventory:
  `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b`
- Field status:
  `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`

It listed all 39 unresolved risk IDs from
`results/common/real_platform_inventory.json` `field_status.unresolved`.

Human decision choices:

- Accept all current risks with a future `human_approval.json`.
- Reject and require stronger experiments or modeling.
- Accept selected listed risk IDs in a future `human_approval.json`.

The request is not consumed by the gate. Empty-context replay must present this
request to the human before creating any future `human_approval.json`.

## Round 8 Review Blocker

Round 8 did not create approval and did not make the real-platform gate pass.
The review kept AC-16 blocked and identified a sidecar consistency bug: the
pre-Round-9 `results/common/real_platform_field_status.json` reported zero
blocking rows even though the gate and quality report treated the 39
`non_identifiable` rows as approval-bound blockers.

The required Round 9 code-worker fix was to count `non_identifiable` as
blocking in the field-status summary, add a regression test, regenerate
real-platform artifacts, and refresh the request hashes and Humanize2 capture
without crossing the approval boundary.

## Round 9 Field-Status Hash Refresh Package

Round 9 code-worker commit:

```text
f6614b00177e4139c8cfcf53b349b69478942b66
```

The Round 9 capture worker is a normalized reconstruction:

- Prompt:
  `artifacts/prompts/round-9-field-status-hash-refresh-worker.md`
- Contract:
  `artifacts/worker_contracts/worker-r9-field-status-hash-refresh.md`
- Output:
  `artifacts/worker_outputs/worker-r9-field-status-hash-refresh.md`
- Verification:
  `artifacts/verification/worker-r9-field-status-hash-refresh.md`
- Tool calls:
  `artifacts/tool_calls/worker-r9-field-status-hash-refresh-normalized.json`

Round 10 approval-bound hashes, preserved as historical context:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `671f5ca4a295aca29a62ee6027b4f6cd756cc49572f0558a98ee8dbf786fbe37` |
| `results/common/real_platform_field_status.json` | `0146ac9ce41185d776f70a8573f8792f7e14a4d58d3f29d36ac7faa1f9f82195` |
| `results/common/search_model_real_platform.json` | `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73` |
| `results/common/experiment_quality.md` | `b63c3bfa1d9c943660a21b3427bc3b9f3402ee6fe6fc5d7a8af5014e197ebb1e` |

Request state:

- `round`: 9
- `request_worker`: `Round9FieldStatusHashRefresh`
- `status`: pending
- `request_status`: not approved
- `decision_status`: not approved
- `gate_status`: not submitted
- `approved`, `is_gate_input`, `is_approval_artifact`, and `gate_consumed`:
  false
- `risk_ids` and `risk_scope.risk_ids`: the exact 39 IDs from
  `results/common/real_platform_inventory.json` `field_status.unresolved`

Round 9 validation commands:

```bash
python3 - <<'PY'
import glob, json
from pathlib import Path
import yaml
for path in ['results/common/agentic_flow/h2_primitives.yaml'] + glob.glob('results/common/agentic_flow/boards/*.yaml'):
    with open(path, 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
for path in glob.glob('results/common/agentic_flow/artifacts/tool_calls/*.json') + ['results/common/real_platform_risk_acceptance_request.json']:
    with open(path, 'r', encoding='utf-8') as f:
        json.load(f)
with open('results/common/agentic_flow/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            json.loads(line)
PY
python3 - <<'PY'
import hashlib, json
from pathlib import Path
inv = json.loads(Path('results/common/real_platform_inventory.json').read_text())
status = json.loads(Path('results/common/real_platform_field_status.json').read_text())
req = json.loads(Path('results/common/real_platform_risk_acceptance_request.json').read_text())
expected_hashes = {
    'inventory_sha256': hashlib.sha256(Path('results/common/real_platform_inventory.json').read_bytes()).hexdigest(),
    'real_platform_field_status_sha256': hashlib.sha256(Path('results/common/real_platform_field_status.json').read_bytes()).hexdigest(),
    'search_model_real_platform_sha256': hashlib.sha256(Path('results/common/search_model_real_platform.json').read_bytes()).hexdigest(),
    'experiment_quality_sha256': hashlib.sha256(Path('results/common/experiment_quality.md').read_bytes()).hexdigest(),
}
ids = [row['risk_id'] for row in inv['field_status']['unresolved']]
assert status['summary']['blocking_total'] == 39
assert status['summary']['blocking_status_counts']['non_identifiable'] == 39
assert req['round'] == 9
assert req['request_worker'] == 'Round9FieldStatusHashRefresh'
assert req['status'] == 'pending'
assert req['request_status'] == 'not_approved'
assert req['decision_status'] == 'not_approved'
assert req['gate_status'] == 'not_submitted'
assert req['approved'] is False
assert req['is_gate_input'] is False
assert req['is_approval_artifact'] is False
assert req['gate_consumed'] is False
assert req['current_hashes'] == expected_hashes
assert req['risk_ids'] == ids
assert req['risk_scope']['risk_ids'] == ids
assert len(ids) == 39
assert not list(Path('results/common').glob('*approval*'))
PY
python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
git diff --check
```

At the Round 9 boundary, the real-platform gate remained expected to return
nonzero until a machine-readable human approval artifact existed, covered the
39 unresolved field-status risks, bound the then-current inventory and
field-status hashes, and the quality report said `Gate status: PASS`.

## Round 10 Focused Evidence Refresh Package

Round 10 evidence commits:

```text
f3bb455245cce28b1f61fd7447e1056e5c9903b2  Add T20 m4 no-reuse ProcResource evidence
cd71b7ed3aa9d222306af23a51fe87efd76eddf9  Add targeted run_suite selection filters
c1032a2c01949ecb9d651473dec1aa88695bb484  Add focused T12 scalar-filler evidence path
73b99c2e1e95ed7828c5ce76d750a909bc83b5c5  Refresh real-platform focused evidence
```

The Round 10 capture worker is a normalized reconstruction:

- Prompt:
  `artifacts/prompts/round-10-focused-evidence-capture-worker.md`
- Contract:
  `artifacts/worker_contracts/worker-r10-capture.md`
- Output:
  `artifacts/worker_outputs/worker-r10-capture.md`
- Verification:
  `artifacts/verification/worker-r10-capture.md`
- Tool calls:
  `artifacts/tool_calls/worker-r10-capture-normalized.json`
- Coordinator output:
  `artifacts/worker_outputs/coordinator-r10-focused-evidence.md`
- Coordinator verification:
  `artifacts/verification/coordinator-r10-focused-evidence.md`
- Coordinator tool calls:
  `artifacts/tool_calls/coordinator-r10-focused-evidence.json`

Current approval-bound hashes:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `728e0fd4570dc92e28f1683123bfde3e07d3903dbe026abc745766c0e06e0231` |
| `results/common/real_platform_field_status.json` | `9669b1f7ab8881d22d9a3072d0a9fe8fbe70654f8d1b6a3d75c9a37e184eed6b` |
| `results/common/search_model_real_platform.json` | `bf06a095edff3a56d03e3cb4223b590834783964ec7c19eaf2f876facdf9d623` |
| `results/common/experiment_quality.md` | `1a46e7ebfdbe692b3be557cad5c05bcbbc89812cf5c6f886f98a6b314f492fae` |

Request state:

- `round`: 10
- `request_worker`: `Round10FocusedEvidenceRefresh`
- `status`: pending
- `request_status`: not approved
- `decision_status`: not approved
- `gate_status`: not submitted
- `approved`, `is_gate_input`, `is_approval_artifact`, and `gate_consumed`:
  false
- `risk_ids` and `risk_scope.risk_ids`: the exact 38 IDs from
  `results/common/real_platform_inventory.json` `field_status.unresolved`

Round 10 incremental real gem5 commands:

```bash
python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T20_PAIRWISE_PIPE_CLASSIFICATION --id-regex 'resource-noreuse$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor
python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T12_CONSUMER_RAW_GAP --id-regex 'fscalar-add$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor
```

Round 10 regeneration and verification commands captured from the coordinator:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results --aggregate results/common/experiment_quality.md --mismatch-report results/common/mismatch_report.md --inventory results/common/real_platform_inventory.json
python3 -m unittest tests.test_run_suite_selection tests.test_gen_asm_t20_coverage tests.test_gen_asm_t12_focused tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval
python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py
python3 -m pytest -q
```

The unit-test and pytest commands passed with 33 tests. Synthetic gate passed.
At the Round 10 boundary, the real-platform gate remained expected to return
nonzero until a machine-readable human approval artifact covered the 38
unresolved field-status risks and bound the then-current inventory and
field-status hashes.

## Replay Commands

### Environment and Generation

The strict environment check is:

```bash
python3 scripts/check_env.py
```

Dry-run replay must opt in to relaxed tool checks and must not be used as real
platform evidence:

```bash
python3 scripts/check_env.py --allow-dry-run-missing-tools
python3 scripts/check_env.py --command dry_run
```

Regenerate the experiment suite metadata without executing gem5:

```bash
python3 scripts/gen_asm.py suite --output-root experiments/generated
python3 scripts/gen_asm.py suite --manifest-only
```

### Synthetic Calibration

```bash
python3 scripts/run_suite.py --all --backend synthetic_cmodel --results-root results
python3 scripts/analyze.py --all --root results
python3 scripts/search_model.py --profile results --output results/common/search_model_summary.md --format markdown
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
```

The synthetic gate is the only path that justified the existing LLVM
YuShuXin implementation evidence. It is not approval for real-platform timing
claims.

### Real-Platform Analysis and Search

Do not run heavy gem5 as part of a lightweight replay. To re-analyze checked-in
real traces:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search-current.json --format json
python3 -m json.tool /tmp/profile-inst-latency-real-search-current.json >/dev/null
cmp /tmp/profile-inst-latency-real-search-current.json results/common/search_model_real_platform.json
python3 scripts/analyze.py --all --root results
```

The Round 4 checked-in artifact regeneration used:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results
```

### Gates and Integrity Checks

```bash
python3 -m json.tool results/common/search_model_real_platform.json >/dev/null
python3 -m json.tool results/common/real_platform_field_status.json >/dev/null
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 -m json.tool results/common/real_platform_risk_acceptance_request.json >/dev/null
find results/r01 results/r02 -name trace.json | wc -l
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
find results/common -maxdepth 1 -iname '*approval*' -print
```

The real-platform gate is expected to fail closed until the report contains an
exact `Gate status: PASS` line and a machine-readable human approval artifact
is created under `results/common` with the current hashes and accepted risk
scope. No approval artifact exists in this capture.

## Round History

### Round 0-1

Initial workers A-H built the synthetic calibration path, gem5 T01 kill-check,
Humanize2 capture scaffold, and gated LLVM YuShuXin evidence. Round 1 replay
state was valid only for synthetic calibration plus T01 real gem5 coverage.

### Round 2

Round 2 implemented the first shared real-platform candidate simulator in
`scripts/search_model.py` and regenerated real-platform search, field-status,
inventory, quality, and profile sidecars. The review kept the round blocked
because non-chainable T11 placeholders were still used as latency evidence,
T20 was not a hard resource constraint, `vcpop_m` LMUL m4 still had conflicts,
and explicit approval was absent.

### Round 3

Round 3 generated expanded T20 pair-count sweeps, added `vcpop_m` LMUL m4
diagnostics, removed non-chainable T11 suite emissions, ran the missing real
gem5 coverage, and regenerated real-platform artifacts. It reached 7190
checked-in r01/r02 traces and 3595/3595 stable repeat groups. The review still
blocked completion because T20 was recorded but skipped by the candidate
simulator, T12 latency readiness was absent, and approval was absent.

### Round 4

Round 4 added focused tests, subject-owned T20 candidate checks, T12
clean-prefix exact/upper-bound constraints, solver-context preservation, and a
fresh real-platform artifact regeneration. Current field status is 150 rows:
111 inferred and 39 non-identifiable, with no conflict or insufficient-evidence
rows. The review kept AC-9 partial because peer-only T20 rows are not
constrained and T12 exactness needs a short-sweep guard. It reopened AC-12 and
AC-13 because this capture tree still described Round 1/T01-only state.

### Round 5 Boundary

Worker Anscombe owned `scripts/search_model.py`,
`tests/test_search_model_candidate_sim.py`, generated real-platform outputs,
common real-platform JSON/Markdown artifacts, and
`results/vredsum_vs/profile.real_platform.yaml`. Current `main` includes that
worker's commit `773f27d6`; Round 5 review accepted the candidate-simulator
fixes for peer-side T20 mirroring and the T12 short-sweep guard.

The Round 6 code-worker capture package owned only
`results/common/agentic_flow/**`. It recorded the missing Round 5 code-worker
control flow and replay commands, did not resolve the 39 non-identifiable rows
by approval, and did not cross the explicit approval boundary.

### Round 6 Approval Gate

Worker Gibbs hardened the real-platform approval gate at commit `ea7c0aca`.
Round 6 review accepted the code behavior and reproduced the expected
fail-closed real-platform gate. The current approval boundary must bind the
Round 6 inventory hash `4f25f066...`, field-status hash `904cca46...`, and
accepted risk scope for the 39 unresolved `non_identifiable` rows.

### Round 7 Capture

The first Round 7 commit `e175258a` captured the missing Round 6 Gibbs control
flow and replay commands. The request-worker then created
`results/common/real_platform_risk_acceptance_request.json` and updated the
Humanize2 capture so empty-context replay presents the request to the human
before any future `human_approval.json` is created. This request does not
create approval, is not consumed by the gate, and does not cross the explicit
approval boundary.

### Round 8 Review

Round 8 recorded the blocked handoff state and did not create approval. The
review kept AC-16 blocked because the real-platform gate still failed closed.
It also found that the field-status sidecar undercounted approval-bound rows:
the sidecar had 39 `non_identifiable` rows but did not include them in
`blocking_total`.

### Round 9 Refresh

Round 9 code-worker commit `f6614b00` fixed the field-status summary so
`non_identifiable` rows are blocking, added a regression test, regenerated the
real-platform artifacts, and refreshed request hashes. This capture package
updates the request metadata to `Round9FieldStatusHashRefresh`, records current
hashes, and keeps the request pending, not approved, and not gate-consumed.

### Round 10 Focused Evidence Refresh

Round 10 added T20 m4 no-reuse ProcResource evidence, targeted run-suite
selection filters, focused T12 scalar-filler evidence, and refreshed checked-in
real-platform artifacts. The unresolved field-status risk count fell from 39
to 38 because `viota_m` `m4` `Latency` is now inferred as candidate `4`.
The active request metadata is `Round10FocusedEvidenceRefresh`; it remains
pending, not approved, not a gate input, and not gate-consumed.

### Round 11 Current-Head Capture

Post-Round-10 commits changed the real-platform evidence boundary again:

- `77d181af` canonicalized pure global ProcResource mirror assignments.
- `6ff16b7c` added matched T12 control experiments, but the controls did not
  justify exact latency claims.
- `88c9e6e5` added focused `vcpop_m` `m4` R11 diagnostics; the proposed
  boundary model was falsified, so issue/resource rows remain fail-closed.
- `8ec7a8a8` fixed real-platform search reproduction: the documented `/tmp`
  output command now matches the checked-in search artifact byte-for-byte and
  does not mutate tracked `results/common` files.

Current artifacts report 150 field rows: 141 inferred and 9
`non_identifiable`, with 0 conflict and 0 insufficient-evidence rows. The
pending request is now Round 11 / `Round11VcpopM4IssueFieldDiagnostics`; it is
not approved, not a gate input, not an approval artifact, and not gate-consumed.

Current hashes:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `197787ab2389df7a059aa9221a70dc5c03c4a18f7dade0c605aca939faa671fd` |
| `results/common/real_platform_field_status.json` | `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432` |
| `results/common/search_model_real_platform.json` | `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6` |
| `results/common/experiment_quality.md` | `d3c2e41f9bcd1a3b92ed2e148be5929d82a8ae111486c7471755030f7af1a31a` |

Reproduction commands:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-current-review-search-fixed.json --format json
cmp /tmp/profile-inst-latency-current-review-search-fixed.json results/common/search_model_real_platform.json
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
```

The real-platform gate is expected to fail closed until the human explicitly
approves the current hashes and exact 9-risk scope, or stronger evidence
resolves those rows.

### Round 12 T12 Exactness Fix

Round 10 review found that matched-control T12 exact latency could be
overclaimed when filler cadence was greater than 1. Commit `91201d20` fixed
the rule: exact latency is now inferred from all positive-stall equations
`gap * cadence + stall`, all positive stalls must agree, and zero-stall
convergence must be consistent with the inferred value. A cadence-2 case with
stalls `[3, 1, 0, 0]` now infers `Latency = 3`; a disagreement case fails
closed as `non_identifiable`.

The current real-platform search artifact remains byte-reproducible against
`results/common/search_model_real_platform.json`, so the request-bound hashes
above did not change. The real-platform gate still fails closed for AC-16
because no approval artifact exists and the same 9 unresolved
`non_identifiable` rows remain approval-bound.

## Humanize2 Hub Path

If a Humanize2 hub is available, load:

```text
results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html
```

Deliver `docs/plan.md` as the implementation-plan artifact and this file as the
replay artifact. Boards under `results/common/agentic_flow/boards/` provide the
current persistent state.

## Resume After Failure

1. Read `events.jsonl` to find the latest captured event and active round.
2. Read `boards/execution_state.yaml` for active mode, gate status, and owned
   write boundaries.
3. Read `boards/inference_state.yaml` for real-platform artifact hashes,
   current field-status counts, the pending request artifact, and replay
   commands.
4. Read `.humanize/rlcr/2026-05-23_01-15-03/round-*-prompt.md`,
   `round-*-summary.md`, and `round-*-review-result.md` for the exact RLCR
   prompt/result lineage.
5. Re-run only the failed lightweight check or worker-owned package. Do not run
   heavy gem5 unless the active worker explicitly owns that task.
6. If AC-16 is the active topic, present
   `results/common/real_platform_risk_acceptance_request.json` to the human
   before creating any future `human_approval.json`.
7. Append a new event and verification artifact before asking the coordinator
   to integrate the result.
