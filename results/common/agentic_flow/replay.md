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

## Plain-Script Fallback

When Humanize2 hub support is unavailable, replay the workflow with the plain
scripts in this order as they become available:

```bash
python3 scripts/check_env.py
python3 scripts/run_suite.py --killcheck
python3 scripts/run_suite.py --all
python3 scripts/analyze.py --all
python3 scripts/search_model.py --profile results
python3 scripts/check_calibration_gate.py --mode synthetic_calibration
python3 scripts/prepare_llvm_yushuxin_worktree.py --tag llvmorg-22.1.3 --cpu YuShuXin
```

The final LLVM worktree command must remain dry-run unless the synthetic gate
passes and the coordinator explicitly chooses to execute it.

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
