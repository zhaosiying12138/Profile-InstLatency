# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vrgather_vv/experiments/t30-vrgather-vv-t12-m2-k24/trace.json`
- Experiment ID: `t30-vrgather-vv-t12-m2-k24`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 70 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 70 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
