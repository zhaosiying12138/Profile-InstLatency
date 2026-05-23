# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vslideup_vx/experiments/t10-vslideup-vx-m2-n8/trace.json`
- Experiment ID: `t10-vslideup-vx-m2-n8`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vslideup_vx`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 55 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 55 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
