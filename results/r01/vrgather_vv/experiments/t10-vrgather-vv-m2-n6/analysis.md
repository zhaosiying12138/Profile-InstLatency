# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vrgather_vv/experiments/t10-vrgather-vv-m2-n6/trace.json`
- Experiment ID: `t10-vrgather-vv-m2-n6`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 36 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 36 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
