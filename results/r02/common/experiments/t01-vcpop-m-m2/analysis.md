# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/common/experiments/t01-vcpop-m-m2/trace.json`
- Experiment ID: `t01-vcpop-m-m2`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 0 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 0 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
