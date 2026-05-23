# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vslideup_vx/experiments/t30-vslideup-vx-t12-m4-k24/trace.json`
- Experiment ID: `t30-vslideup-vx-t12-m4-k24`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vslideup_vx`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 117 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 117 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
