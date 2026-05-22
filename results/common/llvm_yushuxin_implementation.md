# YuShuXin LLVM 22.1.3 Implementation Evidence

## Worktree

- Path: `/home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model`
- Branch: `riscv-yushuxin-sched-model`
- Base tag commit: `llvmorg-22.1.3` / `e9846648fd6183ee6d8cbdb4502213fcf902a211`
- Implementation commits:
  - `16b310c4d2525d193352b729e3e1a84164886cb7` / `RISCV: add YuShuXin RVV schedule model`
  - `13a8f69179f0bb60ff710f03d1032b48ba7389f0` / `RISCV: strengthen YuShuXin RVV mca checks`

## Changed LLVM Files

- `llvm/lib/Target/RISCV/RISCVSchedYuShuXin.td`
- `llvm/lib/Target/RISCV/RISCV.td`
- `llvm/lib/Target/RISCV/RISCVProcessors.td`
- `llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s`
- `llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll`

## Calibration Gate Prerequisite

The LLVM worktree evidence was accepted only after
`python3 scripts/check_calibration_gate.py --mode synthetic_calibration
--profile-root results --mismatch-report results/common/mismatch_report.md`
reported `PASS` with no claimed mismatches. Real Paladin or full gem5 profiling
must still use the real-platform confidence gate instead of golden equality.

## Model Summary

- CPU name: `YuShuXin`
- Registered as an RV64 processor model, not only a tune CPU.
- Default ISA subset: `RV64IM_Zicsr_Zifencei_Zve32x_Zvl128b`.
- LLVM scheduler shape:
  - `IssueWidth = 2`
  - `MicroOpBufferSize = 0`
  - `LoadLatency = 4`
  - RVV resources: `YuShuXinVPipe0`, `YuShuXinVPipe1`, `YuShuXinAnyVPipe`
  - Scalar fallback resource: `YuShuXinScalar`
- Profiled exact RVV scope: 10 non-memory families at `SEW=e32`, `LMUL=m1/m2/m4`.
- Unprofiled RVV and extension families are kept buildable through explicit unsupported fallback resources; this prevents accidental silent precision claims outside the profiled scope.

## Verification Commands

All commands ran from the LLVM worktree.

```bash
/home/zhaosiying/codebase/compiler/build_ysx_host_llvm/bin/llvm-tblgen \
  -I llvm/include -I llvm/lib/Target/RISCV \
  -gen-subtarget llvm/lib/Target/RISCV/RISCV.td \
  -o /tmp/yushuxin-RISCVGenSubtargetInfo.inc
```

Result: passed.

The mca test now checks the exact instruction-table rows for all 30 profiled
RVV instruction/LMUL combinations, including latency, reciprocal throughput,
and RVV pipe resource/ReleaseAtCycles display.

```bash
cmake -G Ninja -S llvm -B /tmp/yushuxin-llvm-build \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_TARGETS_TO_BUILD=RISCV \
  -DLLVM_ENABLE_PROJECTS= \
  -DLLVM_INCLUDE_TESTS=ON \
  -DLLVM_INCLUDE_BENCHMARKS=OFF \
  -DLLVM_BUILD_TESTS=OFF \
  -DLLVM_BUILD_EXAMPLES=OFF
ninja -C /tmp/yushuxin-llvm-build llc llvm-mca FileCheck
```

Result: passed after the CPU was changed from tune-only to a real RV64 processor model and `ReadVISlideV` was moved out of unsupported fallback.

```bash
/tmp/yushuxin-llvm-build/bin/llvm-mca \
  -mtriple=riscv64 -mcpu=YuShuXin -mattr=+v,+zvl128b \
  -iterations=1 -instruction-tables=full \
  < llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s \
  | /tmp/yushuxin-llvm-build/bin/FileCheck \
      llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s
```

Result: passed.

```bash
sed 's/iXLen/i64/g' llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll \
  | /tmp/yushuxin-llvm-build/bin/llc \
      -mtriple=riscv64 -mcpu=YuShuXin -mattr=+v,+zvl128b \
      -verify-machineinstrs \
  | /tmp/yushuxin-llvm-build/bin/FileCheck \
      llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll
```

Result: passed.

```bash
git diff --check
```

Result: passed before commit.

## Debug Notes

- Initial TableGen failed because a partial RVV-only model still must provide resources for scalar schedule writes such as `WriteIALU`.
- Reusing `UnsupportedSchedV` directly was invalid because it duplicated profiled writes such as `WriteVSETVLI`; the final model uses explicit profile writes plus an explicit unsupported fallback subset.
- The initial `llvm-mca` run failed with `RV64 target requires an RV64 CPU`; registering `YuShuXin` as `RISCVProcessorModel` fixed that.
- The first `vslideup.vx` mca run failed because `ReadVISlideV` remained unsupported; moving it to the profiled read-advance set fixed the test.
