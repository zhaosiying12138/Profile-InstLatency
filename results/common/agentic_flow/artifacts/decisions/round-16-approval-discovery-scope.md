# Decision: Round 16 Approval Discovery Scope

Analyzer approval discovery must not be broader than the real-platform gate's
approval-file discovery.

Decision:

- `results/common/human_approval.json`,
  `results/common/human_approval.yaml`, and
  `results/common/human_approval.yml` are the only gate-discoverable approval
  files.
- Analyzer quality reporting uses the same file lookup helper as the gate.
- Nested `results/**/human_approval.*` files are ignored for artifact-level
  approval discovery.

Rationale:

AC-16 requires an explicit machine-readable approval artifact before the real
platform gate can pass. A quality report must not claim approval from a file
that `check_calibration_gate.py` will ignore.

Current result:

- Scope repair commit: `366be5b8`.
- No approval artifact was created.
- The pending risk request remains not approved and not gate-consumed.
- The real-platform gate still fails closed until the 9 unresolved risks are
  resolved by stronger evidence or explicitly accepted by the human owner.
