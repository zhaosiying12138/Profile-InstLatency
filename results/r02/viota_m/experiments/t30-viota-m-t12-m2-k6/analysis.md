# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/viota_m/experiments/t30-viota-m-t12-m2-k6/trace.json`
- Experiment ID: `t30-viota-m-t12-m2-k6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `viota_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 15 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 15 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
