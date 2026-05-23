# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vsll_vv/experiments/t12-vsll-vv-m4-k24-vadd-vv/trace.json`
- Experiment ID: `t12-vsll-vv-m4-k24-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vsll_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 103 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 103 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
