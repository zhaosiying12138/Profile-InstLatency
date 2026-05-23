# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vcpop_m/experiments/t10-vcpop-m-m4-scalar-fixed-n12/trace.json`
- Experiment ID: `t10-vcpop-m-m4-scalar-fixed-n12`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 15 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 15 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
