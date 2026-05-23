# Worker Contract: Round 5 Capture Refresh

Round: 5
Worker: Round5Capture
Owner scope: `results/common/agentic_flow/**`

## Objectives

- Refresh replay, boards, event log, cartridge, manifest notes, and status view
  from stale Round 1/T01-only state to Round 5 boundary state.
- Add prompt, worker-output, verification, and tool-call artifacts for this
  capture refresh.
- Preserve conservative claims at the Round 5 capture-refresh boundary: code
  fixes are owned by another worker and observed at commit `773f27d6`, the
  real-platform gate is fail-closed, and no approval artifact exists.

## Constraints

- Do not edit `scripts/search_model.py`, generated real-platform JSON/Markdown
  outputs, `results/*/profile.real_platform.yaml`, or `.humanize/rlcr/**`.
- Do not create approval artifacts.
- Do not run heavy gem5.
- Validate JSON/YAML syntax, stale Round 1/T01-only wording, and whitespace.

## Required Validation

```bash
python3 -m json.tool results/common/agentic_flow/artifacts/tool_calls/worker-r5-capture-verification.json >/dev/null
python3 - <<'PY'
import json, pathlib
for path in [pathlib.Path('results/common/agentic_flow/events.jsonl')]:
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        json.loads(line)
PY
python3 - <<'PY'
import pathlib, yaml
for path in pathlib.Path('results/common/agentic_flow').glob('boards/*.yaml'):
    yaml.safe_load(path.read_text())
yaml.safe_load(pathlib.Path('results/common/agentic_flow/h2_primitives.yaml').read_text())
PY
if rg -n 'Status: Round 1 replay record|Round 1 capture\. Active worker|it remains `NOT_READY` because only the T01|^round: 0$' results/common/agentic_flow --glob '!**/worker-r5-capture.md' --glob '!**/worker-r5-capture-verification.json'; then exit 1; fi
git diff --check -- results/common/agentic_flow
```
