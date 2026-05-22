# Simulator Candidate Comparison Stub

Status: pending real RVV kill-check evidence.

## Current Baseline

- Candidate: gem5 MinorCPU
- Local executable: `/home/zhaosiying/codebase/compiler/gem5/build/RISCV/gem5.opt`
- Checkout: `/home/zhaosiying/codebase/compiler/gem5`
- Current evidence: executable exists and is configured in `config/paths.yaml`
- Missing evidence: non-dry-run RVV kill-check traces for the selected instruction set

The synthetic dry-run traces under `results/common/experiments/` are workflow
scaffolding evidence only. They must not be treated as real platform profiling
or proof that the current gem5 checkout is RVV-stable.

## Fallback Candidates

| Candidate | Role | Required Evidence Before Selection |
| --- | --- | --- |
| gem5 MinorCPU | Preferred baseline | Non-dry-run kill-check passes for the selected RVV instructions and records trace artifacts. |
| Spike plus timing wrapper | Fallback semantic executor | Can execute the selected RVV instructions and expose enough timestamp or event data for latency experiments. |
| Additional RVV simulator | Fallback comparison path | Documents RVV support, timing observability, and reproducible command lines. |

## Next Decision

Keep gem5 MinorCPU selected while the local executable is present, but hold the
real-platform gate closed until non-dry-run kill-check evidence exists. If the
kill-check fails due to RVV support or stability, update this document with the
failing command, trace path, and the selected fallback candidate.
