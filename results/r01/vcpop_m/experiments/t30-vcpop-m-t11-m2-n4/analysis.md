# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vcpop_m/experiments/t30-vcpop-m-t11-m2-n4/trace.json`
- Experiment ID: `t30-vcpop-m-t11-m2-n4`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 3 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 3 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
