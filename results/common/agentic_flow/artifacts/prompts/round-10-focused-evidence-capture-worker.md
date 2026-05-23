# Prompt Capture: Round 10 Focused Evidence Capture Worker

Prompt ID: round-10-focused-evidence-capture-worker
Task owner: RLCR coordinator
Worker: Round10FocusedEvidenceRefresh
Round: 10
Capture type: normalized reconstruction

This prompt capture records the Humanize2 capture after
commit `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`. Round 10 strengthened the
real-platform evidence set but did not create approval and did not make the
real-platform gate pass.

## Requested Scope

- Capture the Round 10 evidence commits:
  - `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: 108 generated T20 m4
    resource-noreuse experiments and ProcResource evidence/search support.
  - `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: targeted
    `run_suite.py` selection filters.
  - `c1032a2c01949ecb9d651473dec1aa88695bb484`: 54 focused T12
    scalar-filler experiments and conservative diagnostics.
  - `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: incremental real gem5
    refresh, regenerated analysis/search/inventory/quality/request artifacts.
- Record that field status moved from 111 inferred plus 39 non-identifiable to
  112 inferred plus 38 non-identifiable.
- Record the resolved row: `viota_m` `m4` `Latency`, inferred candidate `4`.
- Preserve request semantics: pending, not approved, not submitted, not a gate
  input, not an approval artifact, and not consumed by the gate.
- Bind active Humanize2 state to current hashes:
  - inventory:
    `728e0fd4570dc92e28f1683123bfde3e07d3903dbe026abc745766c0e06e0231`
  - field status:
    `9669b1f7ab8881d22d9a3072d0a9fe8fbe70654f8d1b6a3d75c9a37e184eed6b`
  - real-platform search:
    `bf06a095edff3a56d03e3cb4223b590834783964ec7c19eaf2f876facdf9d623`
  - experiment quality:
    `1a46e7ebfdbe692b3be557cad5c05bcbbc89812cf5c6f886f98a6b314f492fae`
- Refresh Humanize2 primitives, boards, replay notes, manifest notes, status
  panel, cartridge draft, events, worker output, verification, tool-call JSON,
  and coordinator evidence artifacts.
- Record `.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md` as a
  coordinator-owned control-plane artifact, not a worker-owned output.
- Keep AC-16 blocked until explicit current-hash-bound human approval exists
  or stronger evidence resolves all 38 approval-bound risks.

## Write Boundaries

Allowed write set:

- `results/common/agentic_flow/**`
- `results/common/real_platform_risk_acceptance_request.json` only if metadata
  wording is necessary while preserving pending/not-approved/not-gate-input
  semantics.

Forbidden write set:

- Code under `scripts/`
- tests
- generated experiments
- trace results and profile sidecars
- search, field-status, inventory, quality, or mismatch artifacts
- any `.humanize/rlcr/**` control-plane file, including summaries, tracker,
  review results, and state
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
git diff --check
```

BitLesson selector result for both Round 10 subtasks: `LESSON_IDS: NONE`.
