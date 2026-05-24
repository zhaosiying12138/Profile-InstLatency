# Coordinator Round 17 Human Approval Output

The coordinator created `results/common/human_approval.json` after explicit
human approval and regenerated the real-platform inventory and quality report.

The approval is top-level approved, identifies `zhaosiying` as approver, binds
the post-approval inventory hash and current field-status hash, and accepts the
exact 9 unresolved risk IDs. `results/common/real_platform_risk_acceptance_request.json`
was updated to `fulfilled_by_human_approval` while remaining non-gate-consumed.

Gate result:

- Synthetic calibration gate: PASS.
- Real-platform gate: PASS.

The accepted rows remain `non_identifiable`; they are approved known risks, not
newly inferred exact hardware parameters.
