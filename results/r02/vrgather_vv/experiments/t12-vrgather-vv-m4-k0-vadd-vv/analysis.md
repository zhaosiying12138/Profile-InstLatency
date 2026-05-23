# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vrgather_vv/experiments/t12-vrgather-vv-m4-k0-vadd-vv/trace.json`
- Experiment ID: `t12-vrgather-vv-m4-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
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
