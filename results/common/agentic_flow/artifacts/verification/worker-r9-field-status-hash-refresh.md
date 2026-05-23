# Verification: Round 9 Field-Status Hash Refresh Worker

Round: 9
Worker: Round9FieldStatusHashRefresh
Capture type: normalized reconstruction
Status: verification captured for a pending request refresh; not approval

## Required Commands

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

## Expected Results

- YAML, JSON, and JSONL parse checks pass for modified Humanize2 state and all
  tool-call JSON.
- The structural script confirms field-status `blocking_total` is 39,
  `blocking_status_counts.non_identifiable` is 39, request hashes match the
  live files, request risk IDs match inventory order, request status is not
  approved, and no approval artifact exists.
- Unit tests pass.
- Synthetic calibration gate passes.
- Real-platform gate returns nonzero and fails closed on missing
  `Gate status: PASS`, missing machine-readable approval, and 39 unresolved
  `non_identifiable` risks.
- `git diff --check` passes.

This verification intentionally treats a passing real-platform gate as wrong
for this worker, because the refreshed request is still not a gate-satisfying
human approval artifact.

## Observed Results

- YAML/JSON/JSONL parse passed:
  `parse ok: yaml=6 json=15 events=53`.
- Structural check passed:
  `blocking_total=39 non_identifiable=39 risk_ids=39 hashes=current
  approval_files=0`.
- Unit tests passed: `Ran 18 tests in 0.456s`, `OK`.
- Synthetic calibration gate passed:
  `PASS: synthetic_calibration gate passed using
  results/common/mismatch_report.md`.
- Real-platform gate returned exit code 1 and failed closed with:
  missing exact `Gate status: PASS`, missing machine-readable human approval,
  and `unresolved real-platform LLVM field-status risks=39
  status_counts={"non_identifiable": 39}`.
- `git diff --check` passed.
