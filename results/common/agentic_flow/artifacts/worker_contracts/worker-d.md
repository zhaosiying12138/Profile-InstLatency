# Worker D Contract

Worker: D
Round: 0
Backfill source: `artifacts/worker_outputs/worker-d.md`
LESSON_IDS: NONE

## Owned Paths

- `scripts/run_experiment.py`
- `scripts/run_suite.py`
- `scripts/run_killcheck.py`
- `results/common/experiments/**`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-d.md`

## Duties

- Implement runner and suite entrypoint scaffolding.
- Provide dry-run synthetic trace contracts for analyzer development.
- Keep non-dry-run gem5 execution fail-closed until simulator support exists.

## Constraints

- Do not edit `.humanize/rlcr/**`.
- Do not run RLCR setup, gate, or cancel commands.
- Do not edit `docs/plan.md`.
- Do not revert or overwrite other workers' edits.
