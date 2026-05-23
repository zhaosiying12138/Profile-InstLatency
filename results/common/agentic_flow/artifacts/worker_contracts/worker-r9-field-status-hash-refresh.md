# Worker Contract: Round 9 Field-Status Hash Refresh

Round: 9
Worker: Round9FieldStatusHashRefresh
Capture type: normalized reconstruction
Review driver: Round 8 request-changes review and Round 9 code-worker commit
`f6614b00177e4139c8cfcf53b349b69478942b66`
Status: pending request refreshed; not approval

## Objectives

- Refresh the risk-acceptance request metadata from Round 7 to Round 9.
- Preserve the request as pending, not approved, not submitted, not a gate
  input, not an approval artifact, and not consumed by the gate.
- Preserve all 39 unresolved risk IDs in the exact order from
  `results/common/real_platform_inventory.json` `field_status.unresolved`.
- Bind the request and active Humanize2 state to the current Round 9 hashes:
  inventory `671f5ca4a295aca29a62ee6027b4f6cd756cc49572f0558a98ee8dbf786fbe37`,
  field status
  `0146ac9ce41185d776f70a8573f8792f7e14a4d58d3f29d36ac7faa1f9f82195`,
  search `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`,
  and quality
  `b63c3bfa1d9c943660a21b3427bc3b9f3402ee6fe6fc5d7a8af5014e197ebb1e`.
- Record that Round 9 fixed the field-status summary inconsistency:
  `non_identifiable` is counted as blocking and `blocking_total` is 39.
- Capture Round 9 in Humanize2 primitives, boards, events, replay,
  cartridge, status panel, manifest notes, worker output, verification, and
  tool-call JSON.
- Preserve the explicit approval boundary. This worker must not create
  `results/common/human_approval.json` or any approval artifact.

## Owned Write Set

- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/agentic_flow/**`

## Forbidden Write Set

- `.humanize/**`
- `scripts/search_model.py`
- tests
- result profile sidecars
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/common/search_model_real_platform.json`
- any approval artifact under `results/common`

## Required Validation

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

The real-platform gate command is expected to return nonzero. Passing it would
mean the approval boundary changed without explicit human approval, which is
outside this worker's scope.
