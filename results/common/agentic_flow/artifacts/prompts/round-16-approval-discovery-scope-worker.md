# Round 16 Approval Discovery Scope Worker Prompt

Address the current-head approval-discovery scope review finding.

Problem:

- `scripts/analyze_quality.py` discovered `human_approval.*` files anywhere
  under `results/**`.
- `scripts/check_calibration_gate.py` only consumes
  `results/common/human_approval.json`, `results/common/human_approval.yaml`,
  or `results/common/human_approval.yml`.
- A nested approved file under `results/r01/**/human_approval.json` could make
  analyzer quality output report approval even though the real gate still saw
  no approval file.

Required fix:

- Make analyzer discovery and gate validation share the same gate-discoverable
  approval-file helper.
- Keep the approval artifact absent in this workflow; do not create
  `results/common/human_approval.*`.
- Add a regression proving nested approval files are ignored by both analyzer
  discovery and the gate while common approval files retain parity.
- Refresh the Humanize2 capture boundary after the implementation is committed.

Verification to record:

- Focused red/green nested-approval regression.
- Full approval unit tests.
- Full pytest.
- Py-compile for affected scripts.
- `analyze.py --all --dry-run`.
- Synthetic gate pass.
- Real gate fail-closed for the expected AC-16 reasons.
- Real-search byte reproduction against the checked-in search artifact.
