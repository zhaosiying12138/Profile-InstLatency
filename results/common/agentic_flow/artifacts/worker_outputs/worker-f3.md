# Worker F3 Output

Worker: F3
Round: 0 review-fix
LESSON_IDS: NONE

## Status

Complete for the assigned F3 scope.

## Changed Paths

- `scripts/check_env.py`
- `config/paths.yaml`
- `README.md`
- `docs/simulator-candidate-comparison.md`
- `results/common/agentic_flow/boards/execution_state.yaml`
- `results/common/agentic_flow/boards/goal_tracker.yaml`
- `results/common/agentic_flow/events.jsonl`
- `results/common/agentic_flow/h2_primitives.yaml`
- `results/common/agentic_flow/replay.md`
- `results/common/agentic_flow/artifacts/prompts/worker-f3-review-fix.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-a.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-b.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-c.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-d.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-f3.md`
- `results/common/agentic_flow/artifacts/tool_calls/worker-a-verification.json`
- `results/common/agentic_flow/artifacts/tool_calls/worker-b-verification.json`
- `results/common/agentic_flow/artifacts/tool_calls/worker-c-verification.json`
- `results/common/agentic_flow/artifacts/tool_calls/worker-d-verification.json`
- `results/common/agentic_flow/artifacts/tool_calls/worker-f3-red-checks.json`
- `results/common/agentic_flow/artifacts/tool_calls/worker-f3-final-checks.json`
- `results/common/agentic_flow/artifacts/verification/worker-a-verification.md`
- `results/common/agentic_flow/artifacts/verification/worker-b-verification.md`
- `results/common/agentic_flow/artifacts/verification/worker-c-verification.md`
- `results/common/agentic_flow/artifacts/verification/worker-d-verification.md`
- `results/common/agentic_flow/artifacts/verification/worker-f3-red-checks.md`
- `results/common/agentic_flow/artifacts/verification/worker-f3-final-checks.md`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-f3.md`

## Commands Run

- `python3 -m py_compile scripts/check_env.py`
- `python3 scripts/check_env.py`
- `python3 scripts/check_env.py --allow-dry-run-missing-tools`
- `python3 scripts/check_env.py --command dry_run`
- Temporary module check proving default missing `gem5_build` and `assembler`
  fail, while `allow_dry_run_missing_tools=True` passes.
- `grep -RInF 'Only \`check_env.py\` exists in Phase 0' README.md results/common/agentic_flow/replay.md docs`
- JSON validation for `artifacts/tool_calls/*.json` and `events.jsonl`.
- Focused `git diff --check` over Worker F3 owned paths.

## Notes

- `check_env.py` now defaults to strict `plan` validation and requires the
  configured LLVM checkout, gem5 checkout, executable gem5 build, assembler,
  linker, and output root.
- Dry-run/scaffold behavior is explicit through
  `--allow-dry-run-missing-tools` or `--command dry_run`.
- `config/paths.yaml` now points at the verified local
  `/home/zhaosiying/codebase/compiler/gem5/build/RISCV/gem5.opt` and
  `/home/zhaosiying/codebase/software/LLVM-19.1.3-Linux-X64/bin/llvm-mc`.
- Humanize2 capture was backfilled for Workers A-D from existing worker output
  evidence. Worker E already had capture artifacts. Worker F3 prompt, contract,
  red checks, final checks, and output are now recorded.
- Worker outputs for A, B, D, and E record no usable bitlesson entries and no
  unsafe external bitlesson selector run. No bitlesson entries were added.

## Caveats

- The local gem5 executable exists, but current RVV stability for the selected
  instruction set is unproven until a non-dry-run kill-check produces evidence.
- Concurrent uncommitted changes outside the F3 ownership scope were present and
  left unstaged.
