# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vredsum_vs/experiments/t10-vredsum-vs-m1-n4/trace.json`
- Experiment ID: `t10-vredsum-vs-m1-n4`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vredsum_vs`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 3 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 3 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
