# Worker F3 Contract

Worker: F3
Round: 0 review-fix
LESSON_IDS: NONE

## Owned Paths

- `scripts/check_env.py`
- `config/paths.yaml`
- `README.md`
- `docs/simulator-candidate-comparison.md`
- `results/common/agentic_flow/**` capture files
- `results/common/agentic_flow/artifacts/worker_outputs/worker-f3.md`

## Duties

- Enforce strict default environment gating for the real plan path.
- Keep dry-run/scaffold checks explicit through a flag or command mode.
- Use verified local gem5 and LLVM toolchain paths.
- Keep documentation clear that synthetic calibration is not real platform
  profiling.
- Backfill Humanize2 prompt, contract, tool-call, verification, replay, and
  event evidence where current artifacts provide enough support.

## Constraints

- Do not edit `.humanize/**`.
- Do not start, cancel, or gate RLCR.
- Do not edit core runner/analyzer scripts owned by other workers.
- Do not delete other worker outputs.
- Commit only focused changes in the allowed scope.
