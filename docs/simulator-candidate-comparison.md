# Simulator Candidate Comparison

Status: gem5 MinorCPU selected for the first executable kill-check; full
real-platform timing approval is still pending.

## Current Baseline

- Candidate: gem5 MinorCPU
- Local executable: `/home/zhaosiying/codebase/compiler/gem5/build/RISCV/gem5.opt`
- Checkout: `/home/zhaosiying/codebase/compiler/gem5`
- Current evidence: executable exists and is configured in `config/paths.yaml`;
  `scripts/run_suite.py --killcheck --backend gem5_minor --results-root results`
  produced 30 T01 traces covering 10 selected RVV instructions across
  `LMUL=m1/m2/m4`.
- Missing evidence: full T10/T11/T12/T20/T30 latency, release, and resource
  traces from gem5 or hardware with repeatability data.

The synthetic traces under instruction-specific `results/<instr>/experiments/`
remain workflow calibration evidence. The gem5 kill-check proves selected
instruction decode/execute viability, not final latency/resource values.

## Fallback Candidates

| Candidate | Role | Required Evidence Before Selection |
| --- | --- | --- |
| gem5 MinorCPU | Preferred baseline | Full latency/resource suite runs with repeated measurements and approved confidence report. |
| Spike plus timing wrapper | Fallback semantic executor | Can execute the selected RVV instructions and expose enough timestamp or event data for latency experiments. |
| Additional RVV simulator | Fallback comparison path | Documents RVV support, timing observability, and reproducible command lines. |

## Next Decision

Keep gem5 MinorCPU selected while the T01 kill-check remains green. Hold the
real-platform gate closed until the full timing suite has repeated real traces,
documented assumptions, conflict resolution, and human approval.
