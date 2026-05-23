# Worker Contract: Round 7 Risk-Acceptance Request

Round: 7
Worker: Round7RiskRequest
Capture type: normalized self-capture
Review driver: Round 6 review follow-up after commit `e175258a`
Status: pending human decision request; not approval

## Objectives

- Create a machine-readable pending request artifact for current real-platform
  risk acceptance.
- Bind the request to the Round 6 current inventory hash
  `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b`.
- Bind the request to the Round 6 current field-status hash
  `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`.
- Include every unresolved risk ID from
  `results/common/real_platform_inventory.json` `field_status.unresolved`.
- Preserve the approval boundary: the request is not consumed by the gate and
  does not satisfy AC-16.
- Capture this request-worker in Humanize2 artifacts, boards, events, replay,
  cartridge, status panel, and manifest notes.

## Owned Write Set

- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/agentic_flow/**`

## Forbidden Write Set

- `.humanize/**`
- scripts
- tests
- any existing real-platform generated result artifact other than the new
  request JSON
- any new file under `results/common` whose filename contains `approval`

## Required Validation

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

The real-platform gate command is expected to return nonzero. Passing the gate
would be a failure for this worker because this request is not a gate-satisfying
human approval artifact.
