# Synthetic Calibration Mismatch Report

Status: preliminary scaffold.
Mode: synthetic_calibration
Gate status: NOT_READY
Claimed mismatches: none

This report is initialized before any synthetic cmodel traces or inferred profile
fields exist. It therefore makes no calibration claim. The synthetic gate must
remain closed until every claimed inferred field either matches the configured
synthetic value or is explicitly marked not identifiable by the first-version
experiments.

## Instruction Status

| Instruction | Synthetic comparison status | Claimed fields | Notes |
| --- | --- | --- | --- |
| `vadd_vv` | not run | none | Awaiting trace and inferred profile. |
| `vsll_vv` | not run | none | Awaiting trace and inferred profile. |
| `vmul_vv` | not run | none | Awaiting trace and inferred profile. |
| `vdivu_vv` | not run | none | Awaiting trace and inferred profile. |
| `vmseq_vv` | not run | none | Awaiting trace and inferred profile. |
| `vcpop_m` | not run | none | Awaiting trace and inferred profile. |
| `viota_m` | not run | none | Awaiting trace and inferred profile. |
| `vslideup_vx` | not run | none | Awaiting trace and inferred profile. |
| `vrgather_vv` | not run | none | Awaiting trace and inferred profile. |
| `vredsum_vs` | not run | none | Awaiting trace and inferred profile. |

## Simulator Implementation Bugs

No simulator implementation bugs have been observed by this scaffold because no
synthetic traces have been analyzed.

## Experiment Design Limits

- Marker semantics must be validated before any delta is trusted.
- Independent register rotation must be checked for LMUL overlap.
- Mask and passthru operands can create hidden dependencies.
- Scalar frontend limits can masquerade as vector resource occupancy.
- Non-memory experiments must remain isolated from cache and memory effects.

## Follow-Up

1. Populate synthetic traces under `results/**/experiments/**/trace.json`.
2. Run `python3 scripts/analyze.py --all`.
3. Run `python3 scripts/search_model.py` against the timing config and profiles.
4. Update this report with exact matched, mismatched, and not-identifiable fields.
5. Set `Gate status: PASS` only when the synthetic calibration gate truly passes.
