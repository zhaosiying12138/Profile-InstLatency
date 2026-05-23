# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vdivu_vv/experiments/t11-vdivu-vv-m4-n8/trace.json`
- Experiment ID: `t11-vdivu-vv-m4-n8`
- Template ID: `T11_SELF_RAW_CHAIN`
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
