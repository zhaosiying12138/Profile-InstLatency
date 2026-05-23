# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/common/experiments/t01-vslideup-vx-m1/trace.json`
- Experiment ID: `t01-vslideup-vx-m1`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `real_platform_profile`
- Instruction: `vslideup_vx`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 4 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 4 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
