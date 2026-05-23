# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vmul_vv/experiments/t30-vmul-vv-t12-m2-k31/trace.json`
- Experiment ID: `t30-vmul-vv-t12-m2-k31`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 104 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 104 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
