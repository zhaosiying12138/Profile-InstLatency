# Trace JSON Schema

The runner writes one normalized `trace.json` per experiment under
`results/<group>/experiments/<experiment-id>/trace.json`.

## Top-Level Object

```json
{
  "schema_version": 1,
  "experiment_id": "T10-vadd_vv-m1",
  "template_id": "T10_INDEPENDENT_STREAM_THROUGHPUT",
  "mode": "synthetic_calibration",
  "backend": "synthetic_cmodel",
  "dry_run_trace": false,
  "marker_baseline_cycles": 0,
  "synthetic": {
    "timing_model": "config/rvv_timing_model.yaml",
    "instruction_id": "vadd_vv",
    "lmul": "m1",
    "pipe": "any",
    "latency_cycles": 2,
    "release_cycles": 1,
    "measured_delta_cycles": 6
  },
  "entries": [
    {
      "marker": "start",
      "cycle": 1000,
      "pc": "0x80000000",
      "experiment_id": "T10-vadd_vv-m1"
    }
  ]
}
```

Required top-level fields:

- `schema_version`: integer schema version. The initial version is `1`.
- `experiment_id`: stable ID matching the surrounding result directory.
- `template_id`: experiment template ID from `docs/plan.md`.
- `mode`: `synthetic_calibration` for deterministic synthetic cmodel traces,
  or `real_platform_profile` for gem5/hardware traces.
- `backend`: concrete execution backend, for example `synthetic_cmodel` or
  `gem5_minor`.
- `dry_run_trace`: true only when the runner was asked to produce a
  non-executed placeholder trace.
- `marker_baseline_cycles`: constant adjacent-marker delta to subtract before
  analysis. It is `0` for the current zero-cost label marker implementation.
- `entries`: ordered marker entries emitted by the runner.

The `synthetic` object is required only for `backend: synthetic_cmodel`. It
records configured ground truth as post-inference calibration reference; the
analyzer must not use it as the source for LLVM-facing claims.

## Marker Entry

Each `entries` item has this required shape:

```json
{
  "marker": "start",
  "cycle": 1234,
  "pc": "0x80000000",
  "experiment_id": "T10-vadd_vv-m1"
}
```

Field semantics:

- `marker`: marker label from `experiment.yaml` or the template default.
- `cycle`: simulator cycle sampled at the marker.
- `pc`: architectural program counter associated with the marker site.
- `experiment_id`: repeated for join safety when traces are aggregated.

Entries must be sorted in program order. Analyzer code should compute deltas by
label lookup, then subtract `marker_baseline_cycles`.

## Marker Semantics

`TIMESTAMP_MARK <label>` is a simulator observation point, not an instruction
with architectural side effects.

- It samples the current simulator cycle.
- It does not occupy an issue slot.
- It does not enter a functional unit.
- It does not affect scoreboard dependencies.
- It writes to simulator trace/log output, not to architectural registers.

Adjacent markers should produce zero delta. If a future gem5 implementation has
a fixed non-zero marker delta, the runner must record that value in
`marker_baseline_cycles`, and analyzer code must subtract it before fitting
latency or release formulas.

## Synthetic Calibration Mode

Synthetic calibration exists so analyzer, template, and gate logic can be
debugged against a known cmodel before the full gem5 or hardware timing suite is
available.

The synthetic cmodel runner:

- consumes `experiments/generated/<id>/experiment.yaml` and `test.s` when they
  exist;
- writes deterministic marker cycles from `config/rvv_timing_model.yaml`;
- preserves copied `test.s` next to the trace.

Synthetic traces are calibration evidence only. They must not be treated as
measured gem5 or hardware timing results.
