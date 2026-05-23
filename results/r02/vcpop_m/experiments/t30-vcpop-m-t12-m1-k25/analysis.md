# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vcpop_m/experiments/t30-vcpop-m-t12-m1-k25/trace.json`
- Experiment ID: `t30-vcpop-m-t12-m1-k25`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 58 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 58 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
