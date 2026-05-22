# Prompt Capture: Worker F3 Review Fix

Prompt ID: worker-f3-review-fix
Task owner: RLCR coordinator
Worker: F3
Round: 0 review-fix
Time received: 2026-05-23T01:48:54+08:00

## Requested Scope

- Make `scripts/check_env.py` mode-aware and command-aware.
- Configure verified local gem5 and assembler paths in `config/paths.yaml`.
- Update `README.md` so it reflects implemented workflow state and does not
  claim dry-run scaffold acceptance as real platform profiling.
- Backfill Humanize2 capture under `results/common/agentic_flow/**`.
- Add simulator comparison notes if gem5 RVV stability cannot be proven.
- Write `artifacts/worker_outputs/worker-f3.md`.
- Commit the focused change.

## Write Boundaries

Allowed: `scripts/check_env.py`, `config/paths.yaml`, `README.md`,
`docs/simulator-candidate-comparison.md`, selected
`results/common/agentic_flow/**`, and `results/common/processor.yaml` comments
if needed.

Forbidden: `.humanize/**`, RLCR start/cancel/gate commands, core runner and
analyzer scripts owned by other workers, generated experiments, result
profiles/reports.
