# Synthetic Calibration Mismatch Report

Mode: synthetic_calibration
Gate status: PASS
Claimed mismatches: none
Inference source status: non_circular_raw_marker_evidence

Synthetic calibration compares only raw-inferred fields claimed by generated profiles against `config/rvv_timing_model.yaml`. Unknown or not-identifiable fields are explicit in the profiles and are not used as golden-equality claims.

## Instruction Status

| Instruction | Synthetic comparison status | Claimed fields | Notes |
| --- | --- | --- | --- |
| `vadd_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vsll_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vmul_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vdivu_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vmseq_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vcpop_m` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `viota_m` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vslideup_vx` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vrgather_vv` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |
| `vredsum_vs` | matched | asm, latency_formula, m1.latency, m1.pipe_affinity, m1.release_at_cycles, m1.resource_group, m2.latency, m2.pipe_affinity, m2.release_at_cycles, m2.resource_group, m4.latency, m4.pipe_affinity, m4.release_at_cycles, m4.resource_group, release_formula | all claimed raw-inferred fields match config |

## Claimed Field Mismatches

None.

## Experiment Design Limits

- `NumMicroOps`, `SingleIssue`, `ReadAdvance`, and separate writeback stage fields are recorded but unclaimed unless raw markers identify them.
- Synthetic trace metadata is reference-only; it validates mismatches after raw marker inference and is not a source for claims.
- Future real-platform gates must use coverage, stability, confidence, assumptions, conflict resolution, and human approval instead of golden equality.
