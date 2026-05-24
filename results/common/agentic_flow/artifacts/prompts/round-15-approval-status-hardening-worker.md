# Round 15 Approval-Status Hardening Prompt

Address the current-head approval-status review findings.

Requirements:

- Preserve the existing fix from commit `9a85412b`: top-level
  `status: pending` plus nested `risk_acceptance.status: approved` must not be
  accepted as human approval.
- Make analyzer approval discovery and real-platform gate validation use the
  same explicit top-level approval vocabulary.
- Add regression coverage for top-level `human_approved: true` so
  `analyze.discover_approval()` and `human_approval_failures()` agree.
- Keep accepted-risk extraction recursive for nested risk-acceptance scope.
- Do not create `results/common/human_approval.json` or any other approval
  artifact.
- Refresh the Humanize2 capture package for the approval-status hardening
  boundary, including prompt, contract, output, verification, normalized
  tool-call JSON, events, boards, replay, status view, cartridge, and manifest
  notes.

Verification:

- Run the approval-gate unittest module.
- Run py_compile for the affected scripts, including `scripts/approval_status.py`.
- Run full pytest.
- Re-run the synthetic gate.
- Re-run the real-platform gate and confirm it still fails closed for the
  expected missing approval and 9 unresolved risks.
- Confirm no approval artifact exists.
