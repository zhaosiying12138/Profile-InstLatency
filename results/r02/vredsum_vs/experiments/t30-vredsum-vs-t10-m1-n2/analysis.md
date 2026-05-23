# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vredsum_vs/experiments/t30-vredsum-vs-t10-m1-n2/trace.json`
- Experiment ID: `t30-vredsum-vs-t10-m1-n2`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vredsum_vs`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 1 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 1 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
