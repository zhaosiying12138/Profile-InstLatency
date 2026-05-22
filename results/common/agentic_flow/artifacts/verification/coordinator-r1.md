# Verification: Coordinator Round 1

Round: 1
Status: passed for synthetic calibration and gem5 kill-check scope

## Commands

```bash
python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py
python3 scripts/check_env.py
python3 scripts/gen_asm.py suite --output-root experiments/generated
python3 scripts/run_suite.py --all --backend synthetic_cmodel --results-root results
python3 scripts/run_suite.py --killcheck --backend gem5_minor --results-root results
python3 scripts/analyze.py --all --root results
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/search_model.py --profile results --output results/common/search_model_summary.md --format markdown
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results  # expected failure until human-approved full real profile
(cd /home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model && /tmp/yushuxin-llvm-build/bin/llvm-mca -mtriple=riscv64 -mcpu=YuShuXin -mattr=+v,+zvl128b -iterations=1 -instruction-tables=full < llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s | /tmp/yushuxin-llvm-build/bin/FileCheck llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s)
(cd /home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model && sed 's/iXLen/i64/g' llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll | /tmp/yushuxin-llvm-build/bin/llc -mtriple=riscv64 -mcpu=YuShuXin -mattr=+v,+zvl128b -verify-machineinstrs | /tmp/yushuxin-llvm-build/bin/FileCheck llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll)
python3 -m json.tool results/common/agentic_flow/artifacts/tool_calls/coordinator-r1.json >/dev/null
git diff --check
```

## Results

- `results/` contains 3221 `trace.json` files and 3221 `analysis.md` files.
- `experiments/generated/` contains 3221 experiment directories.
- `results/common/experiments/t01-*` contains 30 gem5 MinorCPU traces with
  `backend = gem5_minor`, `mode = real_platform_profile`, and
  `dry_run_trace = false`.
- No generated ASM or result artifact contains the internal marker pseudo op.
- `results/common/mismatch_report.md` reports `Gate status: PASS` and
  `Claimed mismatches: none`.
- `results/common/experiment_quality.md` reports `Gate status: NOT_READY`, as
  expected for partial real-platform evidence.
- LLVM llvm-mca and llc focused tests pass in the YuShuXin LLVM 22.1.3 worktree.
