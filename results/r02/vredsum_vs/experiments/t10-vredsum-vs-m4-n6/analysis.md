# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vredsum_vs/experiments/t10-vredsum-vs-m4-n6/trace.json`
- Experiment ID: `t10-vredsum-vs-m4-n6`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 23 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 23 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
