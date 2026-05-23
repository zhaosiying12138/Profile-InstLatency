# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vdivu_vv/experiments/t30-vdivu-vv-t11-m4-n8/trace.json`
- Experiment ID: `t30-vdivu-vv-t11-m4-n8`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vdivu_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 31 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 31 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
