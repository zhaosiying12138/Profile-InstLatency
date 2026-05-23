# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vrgather_vv/experiments/t12-vrgather-vv-m2-k9-vadd-vv/trace.json`
- Experiment ID: `t12-vrgather-vv-m2-k9-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 26 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 26 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
