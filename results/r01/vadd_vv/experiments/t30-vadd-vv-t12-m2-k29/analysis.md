# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vadd_vv/experiments/t30-vadd-vv-t12-m2-k29/trace.json`
- Experiment ID: `t30-vadd-vv-t12-m2-k29`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vadd_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 98 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 98 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
