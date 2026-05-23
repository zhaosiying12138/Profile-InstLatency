# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vrgather_vv/experiments/t30-vrgather-vv-t12-m2-k39/trace.json`
- Experiment ID: `t30-vrgather-vv-t12-m2-k39`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 123 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 123 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
