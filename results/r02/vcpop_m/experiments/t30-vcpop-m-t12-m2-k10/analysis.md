# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vcpop_m/experiments/t30-vcpop-m-t12-m2-k10/trace.json`
- Experiment ID: `t30-vcpop-m-t12-m2-k10`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 21 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 21 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
