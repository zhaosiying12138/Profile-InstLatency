# Worker G / Coordinator Fallback: LLVM YuShuXin Implementation

## Outcome

- Worker G was closed after hook recursion risk; it did not write LLVM files.
- The coordinator implemented the LLVM 22.1.3 YuShuXin schedule model directly in the isolated worktree.
- LLVM implementation commit: `16b310c4d2525d193352b729e3e1a84164886cb7`
- Worktree: `/home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model`

## Files Implemented

- `llvm/lib/Target/RISCV/RISCVSchedYuShuXin.td`
- `llvm/lib/Target/RISCV/RISCV.td`
- `llvm/lib/Target/RISCV/RISCVProcessors.td`
- `llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s`
- `llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll`

## Verification

- `llvm-tblgen -gen-subtarget` passed.
- Minimal RISC-V LLVM build passed:
  - `ninja -C /tmp/yushuxin-llvm-build llc llvm-mca FileCheck`
- `llvm-mca` YuShuXin RVV schedule test passed.
- `llc -verify-machineinstrs` YuShuXin RVV codegen test passed.
- `git diff --check` passed before the LLVM commit.

## Lessons Captured For Replay

- Use a true `RISCVProcessorModel` when the test triple is `riscv64`; a tune-only CPU lacks `Feature64Bit`.
- A partial RVV schedule model still needs scalar schedule resources because `vsetvli`, `ret`, and generated glue code rely on scalar writes and reads.
- Do not apply `UnsupportedSchedV` wholesale after defining profiled V writes; it creates duplicate `WriteRes` records. Use explicit unsupported fallback definitions for only unprofiled families.
- MC-level RVV instructions use `_WorstCase` schedule writes and reads. The mca test therefore validates `_WorstCase` entries in addition to LMUL-specific pseudo schedule entries.
