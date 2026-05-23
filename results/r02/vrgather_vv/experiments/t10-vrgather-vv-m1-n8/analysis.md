# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vrgather_vv/experiments/t10-vrgather-vv-m1-n8/trace.json`
- Experiment ID: `t10-vrgather-vv-m1-n8`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 17 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 17 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
