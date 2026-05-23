# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vdivu_vv/experiments/t11-vdivu-vv-m2-n12/trace.json`
- Experiment ID: `t11-vdivu-vv-m2-n12`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `real_platform_profile`
- Instruction: `vdivu_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 45 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 45 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
