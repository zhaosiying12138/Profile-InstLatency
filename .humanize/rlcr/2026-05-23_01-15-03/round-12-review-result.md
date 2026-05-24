- [P2] Load profile contents before unpacking them — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/export_llvm_draft.py:45-46
  When `scripts/export_llvm_draft.py` is run with any existing `profile.yaml`, this helper returns only the `Path` objects from `search_model.load_profiles`, but `build_rows()` immediately unpacks each item as `(profile_path, profile)`. The command therefore crashes with `TypeError: cannot unpack non-iterable PosixPath object` instead of exporting the LLVM draft; parse each returned profile path before returning.

- [P2] Honor dry-run before launching gem5 — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/run_experiment.py:1058-1060
  When `--dry-run` is combined with `--backend gem5_minor` (directly or through `run_suite.py`), this branch still assembles and launches gem5, then writes a `real_platform_profile` trace with `dry_run_trace: false`. That breaks the dry-run contract on machines without gem5/toolchain access and silently records non-dry-run output; handle `dry_run` before the gem5 branch or reject the incompatible option combination.

- [P2] Keep default reports under the selected root — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/analyze.py:31-39
  When `--root` is set to a non-default results directory, these defaults still write the quality and mismatch reports under `results/common`. For the documented repeated-run flow such as `--root results_repeat/r01`, analysis will overwrite/report against a different root unless the caller also remembers to pass every output path, and follow-up gates will not find reports colocated with the selected root.
The patch adds useful infrastructure, but at least one advertised script crashes unconditionally with real profiles, and dry-run/report path handling can produce incorrect behavior in supported CLI scenarios.

Full review comments:

- [P2] Load profile contents before unpacking them — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/export_llvm_draft.py:45-46
  When `scripts/export_llvm_draft.py` is run with any existing `profile.yaml`, this helper returns only the `Path` objects from `search_model.load_profiles`, but `build_rows()` immediately unpacks each item as `(profile_path, profile)`. The command therefore crashes with `TypeError: cannot unpack non-iterable PosixPath object` instead of exporting the LLVM draft; parse each returned profile path before returning.

- [P2] Honor dry-run before launching gem5 — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/run_experiment.py:1058-1060
  When `--dry-run` is combined with `--backend gem5_minor` (directly or through `run_suite.py`), this branch still assembles and launches gem5, then writes a `real_platform_profile` trace with `dry_run_trace: false`. That breaks the dry-run contract on machines without gem5/toolchain access and silently records non-dry-run output; handle `dry_run` before the gem5 branch or reject the incompatible option combination.

- [P2] Keep default reports under the selected root — /home/zhaosiying/codebase/compiler/profile_inst_latency/scripts/analyze.py:31-39
  When `--root` is set to a non-default results directory, these defaults still write the quality and mismatch reports under `results/common`. For the documented repeated-run flow such as `--root results_repeat/r01`, analysis will overwrite/report against a different root unless the caller also remembers to pass every output path, and follow-up gates will not find reports colocated with the selected root.
