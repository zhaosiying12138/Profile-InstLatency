# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/common/experiments/t01-vrgather-vv-m4/trace.json`
- Experiment ID: `t01-vrgather-vv-m4`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 19 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 19 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
