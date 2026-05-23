# Verification: Round 7 Risk-Acceptance Request Worker

Round: 7
Worker: Round7RiskRequest
Capture type: normalized self-capture
Status: verification captured for a pending request artifact; not approval

## Required Commands

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('results/common/real_platform_risk_acceptance_request.json').read_text())
assert len(data['risk_ids']) == 39
for key, value in data.items():
    if key.endswith('status') or key in {'status', 'approved'}:
        lowered = str(value).lower()
        assert lowered not in {'approved', 'true', 'yes', 'pass'}
assert data.get('approved') is False
assert data.get('is_approval_artifact') is False
assert data.get('gate_consumed') is False
PY
find results/common -maxdepth 1 -iname '*approval*' -print
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
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
with open('results/common/agentic_flow/h2_primitives.yaml', 'r', encoding='utf-8') as f:
    primitives = yaml.safe_load(f)
for entry in primitives.get('artifacts', []):
    path = entry.get('path', '')
    if path and not path.startswith('../../../'):
        assert Path('results/common/agentic_flow', path).exists(), path
PY
rg 'real_platform_risk_acceptance_request|4f25f066|904cca46|39 unresolved' results/common/agentic_flow results/common/real_platform_risk_acceptance_request.json
git diff --check
```

## Expected Results

- The request JSON parses, contains exactly 39 risk IDs, and has no approved or
  truthy status.
- `find results/common -maxdepth 1 -iname '*approval*' -print` returns empty.
- The real-platform gate fails closed on missing `Gate status: PASS`, missing
  machine-readable human approval, and 39 unresolved `non_identifiable` risks.
- `h2_primitives.yaml` and all board YAML parse.
- All tool-call JSON and the request JSON parse.
- `events.jsonl` parses line by line.
- All registered local Humanize2 artifact paths exist.
- `rg` finds the request path, current hashes, and 39 unresolved-risk language.
- `git diff --check` passes.

This verification intentionally treats a passing real-platform gate as wrong
for this worker, because the request is not a gate-satisfying human approval
artifact.

## Observed Results

- Request JSON shape check passed:
  `request json ok: 39 risk ids; pending/not approved; not gate consumed`.
- `find results/common -maxdepth 1 -iname '*approval*' -print` returned empty
  output.
- Real-platform gate returned exit code 1 and failed closed with:
  missing exact `Gate status: PASS`, missing machine-readable human approval,
  and `unresolved real-platform LLVM field-status risks=39
  status_counts={"non_identifiable": 39}`.
- YAML parse passed for `h2_primitives.yaml` and all board YAML.
- JSON parse passed for all tool-call JSON and the request JSON.
- `events.jsonl` parsed as 46 events.
- Registered Humanize2 path existence check covered 62 registered paths.
- Current-reference `rg` check passed.
- `git diff --check` passed.
