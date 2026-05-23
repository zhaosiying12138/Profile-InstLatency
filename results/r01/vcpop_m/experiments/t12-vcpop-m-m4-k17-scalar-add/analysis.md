# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vcpop_m/experiments/t12-vcpop-m-m4-k17-scalar-add/trace.json`
- Experiment ID: `t12-vcpop-m-m4-k17-scalar-add`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vcpop_m`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 69 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 69 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
