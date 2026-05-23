# Verification: Round 10 Focused Evidence Capture Worker

Round: 10
Worker: Round10FocusedEvidenceRefresh
Capture type: normalized reconstruction
Status: verification for capture-only metadata; not approval

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
assert status['summary']['blocking_total'] == 38
assert status['summary']['blocking_status_counts']['non_identifiable'] == 38
assert req['round'] == 10
assert req['request_worker'] == 'Round10FocusedEvidenceRefresh'
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
assert len(ids) == 38
assert not list(Path('results/common').glob('*approval*'))
PY
python3 - <<'PY'
from pathlib import Path
summary = Path('.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md').read_text()
required = [
    '## Work Completed',
    '## Files Changed',
    '## Validation',
    '## Remaining Items',
    '## Goal Tracker Update Request',
    '## BitLesson Delta',
    '- Action: none',
    '- Lesson ID(s): NONE',
]
for marker in required:
    assert marker in summary, marker
PY
find results/common -maxdepth 1 -name 'human_approval.*' -print
git diff --check
git diff --cached --check
```

## Expected Results

- YAML, JSON, and JSONL parse checks pass for modified Humanize2 state and all
  tool-call JSON.
- Structural check confirms field-status `blocking_total` is 38, request
  hashes match live files, request risk IDs match inventory order, request is
  not approved, and no approval artifact exists.
- Summary formatting includes the required sections and BitLesson Delta.
- `git diff --check` and `git diff --cached --check` pass.

This verification intentionally treats a passing real-platform gate as outside
scope, because the request is still not a gate-satisfying approval artifact.

## Observed Results

- YAML/JSON/JSONL parse passed:
  `parse ok: yaml=6 json=17 events=60`.
- HTML parse passed for the status panel and cartridge draft:
  `html parse ok: 2`.
- Structural check passed:
  `blocking_total=38 non_identifiable=38 risk_ids=38 hashes=current
  human_approval_files=0`.
- Summary section check passed:
  `summary format ok`.
- `git diff --check` passed.
- `git diff --cached --check` passed.
