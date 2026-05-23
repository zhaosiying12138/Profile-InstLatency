# Verification: Round 5 Capture Refresh

Round: 5
Worker: Round5Capture
Status: passed

## Commands

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
find results/r01 results/r02 -name trace.json | wc -l
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
python3 - <<'PY'
import json, collections
from pathlib import Path
rows=json.loads(Path('results/common/real_platform_field_status.json').read_text()).get('rows', [])
print('rows', len(rows))
print(dict(collections.Counter(r.get('status') for r in rows)))
PY
find results/common -maxdepth 1 -iname '*approval*' -print
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results; status=$?; echo exit_code=$status; test $status -ne 0
git diff --check -- results/common/agentic_flow
git diff --check
```

## Results

- Tool-call JSON parsed successfully.
- `events.jsonl` parsed successfully as JSONL.
- Board YAML files and `h2_primitives.yaml` parsed successfully with PyYAML.
- All primitive manifest paths in `templates`, `boards`, and `artifacts` exist.
- The exact stale-claim grep returned no matches.
- Trace-count check returned `7190`.
- Historical Round 5 boundary hashes:
  - `results/common/real_platform_inventory.json`: `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d`
  - `results/common/real_platform_field_status.json`: `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
  - `results/common/search_model_real_platform.json`: `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
  - `results/common/experiment_quality.md`: `6062c76f6f051eac6c60b0ead3be0e8ac74bc3f723841a0ec19d0d7a750e7307`
- Field-status count check returned 150 rows: 111 inferred and 39
  non-identifiable.
- Approval artifact search returned no paths.
- Synthetic calibration gate passed.
- Real-platform gate failed closed as expected with exit code 1 because
  `Gate status: PASS` and machine-readable approval are absent.
- `git diff --check -- results/common/agentic_flow` returned success.
- `git diff --check` returned success.
