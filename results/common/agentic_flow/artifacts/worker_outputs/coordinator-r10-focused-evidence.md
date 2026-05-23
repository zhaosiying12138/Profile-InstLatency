# Coordinator Round 10 Focused Evidence Output

Round: 10
Owner: RLCR coordinator
Status: stronger real-platform evidence refreshed; real gate still fail-closed

## Changes Integrated

- Added 108 generated T20 m4 resource-noreuse experiments and global
  ProcResource evidence/search support in
  `f3bb455245cce28b1f61fd7447e1056e5c9903b2`.
- Added targeted `run_suite.py` filters for `--template-id`, `--id-regex`, and
  `--missing` in `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`.
- Added 54 focused T12 scalar-filler experiments and conservative T12
  diagnostics in `c1032a2c01949ecb9d651473dec1aa88695bb484`.
- Ran incremental real gem5 for the new T20 and T12 evidence with repeat 2,
  then regenerated real-platform search, profile, inventory, quality, and
  request artifacts in `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`.

## Evidence State

- Checked-in `results/r01` and `results/r02` trace files: 7514.
- Required real gem5 groups: 178/178 covered.
- Repeatability: 3757 stable groups, 0 unstable groups.
- Field status: 150 rows, 112 inferred, 38 non-identifiable, 0 conflict, 0
  insufficient-evidence.
- Newly resolved row: `viota_m` `m4` `Latency`, inferred candidate `4`.

## Current Hashes

- `results/common/real_platform_inventory.json`:
  `728e0fd4570dc92e28f1683123bfde3e07d3903dbe026abc745766c0e06e0231`
- `results/common/real_platform_field_status.json`:
  `9669b1f7ab8881d22d9a3072d0a9fe8fbe70654f8d1b6a3d75c9a37e184eed6b`
- `results/common/search_model_real_platform.json`:
  `bf06a095edff3a56d03e3cb4223b590834783964ec7c19eaf2f876facdf9d623`
- `results/common/experiment_quality.md`:
  `1a46e7ebfdbe692b3be557cad5c05bcbbc89812cf5c6f886f98a6b314f492fae`

## Gate State

Synthetic calibration passed. The real-platform gate remains expected to fail
closed because the machine-readable human approval artifact is absent and 38
LLVM-facing field-status risks remain unresolved as `non_identifiable`.
