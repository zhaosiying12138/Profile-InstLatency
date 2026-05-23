# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vadd_vv/experiments/t30-vadd-vv-t11-m2-n4/trace.json`
- Experiment ID: `t30-vadd-vv-t11-m2-n4`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vadd_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 13 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 13 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
