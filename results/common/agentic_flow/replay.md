# Humanize2 Replay Notes

Status: preliminary Round 0 capture.

## Checkout

Use the profiling checkout:

```bash
cd /home/zhaosiying/codebase/compiler/profile_inst_latency
```

The LLVM source checkout referenced by the plan is:

```bash
/home/zhaosiying/codebase/compiler/llvm-project-21
```

## Modes

- `synthetic_calibration`: use configured cmodel ground truth to repair
  templates, prompts, schemas, inference, and mismatch reporting.
- `real_platform_profile`: do not use golden equality. Stop on coverage,
  stability, confidence, assumptions, conflict resolution, and human approval.

## Environment Gate

The default environment check is the strict plan path:

```bash
python3 scripts/check_env.py
```

It requires the configured LLVM checkout, gem5 checkout, gem5 executable,
assembler, linker, and output root. Dry-run and scaffold replay must opt in to
relaxed tool checks:

```bash
python3 scripts/check_env.py --allow-dry-run-missing-tools
python3 scripts/check_env.py --command dry_run
```

Relaxed checks do not prove real platform profiling readiness.

## Plain-Script Fallback

When Humanize2 hub support is unavailable, replay the workflow with the plain
scripts in this order as they become available:

```bash
python3 scripts/check_env.py
python3 scripts/gen_asm.py suite --manifest-only
python3 scripts/run_suite.py --killcheck
python3 scripts/run_suite.py --all
python3 scripts/analyze.py --all
python3 scripts/search_model.py --profile results
python3 scripts/check_calibration_gate.py --mode synthetic_calibration
python3 scripts/prepare_llvm_yushuxin_worktree.py --tag llvmorg-22.1.3 --cpu YuShuXin
```

The final LLVM worktree command must remain dry-run unless the synthetic gate
passes and the coordinator explicitly chooses to execute it.

For scaffold-only replay, add `--dry-run` to `run_suite.py` and do not use the
result as real platform evidence.

## Humanize2 Hub Path

If a Humanize2 hub is available, load:

```text
results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html
```

Deliver `docs/plan.md` as the implementation-plan artifact and this file as the
replay artifact. Boards under `results/common/agentic_flow/boards/` provide the
initial persistent state.

## Resume After Failure

1. Read `events.jsonl` to find the last completed event.
2. Read `boards/execution_state.yaml` for active mode and gate status.
3. Read `boards/inference_state.yaml` for the analysis/search/gate inputs.
4. Re-run only the failed script or worker package.
5. Append a new event and verification artifact before asking the coordinator to
   integrate the result.

## Captured Worker Evidence

- Worker A-D contracts and verification records were backfilled from their
  existing `artifacts/worker_outputs/worker-*.md` reports.
- Worker E already had a prompt-adjacent contract, red checks, final checks, and
  output artifacts.
- Worker F3 adds the review-fix prompt, contract, red checks, and final report.
- `.humanize/bitlesson.md` was reported as containing no lesson entries by
  Workers A, B, D, and E. The unsafe external bitlesson selector was not run, so
  no bitlesson entries were added to this replay.
- `docs/simulator-candidate-comparison.md` records that the local gem5
  executable is configured but RVV stability is still unproven until non-dry-run
  kill-check evidence exists.
