# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vslideup_vx/experiments/t30-vslideup-vx-t10-m1-n4/trace.json`
- Experiment ID: `t30-vslideup-vx-t10-m1-n4`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vslideup_vx`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 19 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 19 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
