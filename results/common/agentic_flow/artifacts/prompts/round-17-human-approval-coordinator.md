# Round 17 Human Approval Coordinator Prompt

## Input

The human owner approved the 9 current `non_identifiable` real-platform
LLVM-facing risks after reviewing the risk IDs and artifact hashes.

## Required Coordinator Actions

1. Create `results/common/human_approval.json` as the only gate-discoverable
   approval artifact.
2. Bind the approval to the current post-approval inventory hash, field-status
   hash, search hash, quality-report hash, request hash, approver identity, and
   exact accepted risk IDs.
3. Regenerate real-platform inventory and quality artifacts with
   `python3 scripts/analyze.py --all`.
4. Verify that both synthetic and real-platform gates pass.
5. Capture the approval decision and gate transition in Humanize2 artifacts.

## Forbidden Actions

- Do not infer exact hardware values for the 9 accepted risks.
- Do not treat `real_platform_risk_acceptance_request.json` as a gate input.
- Do not edit `.humanize/rlcr/**`; request tracker updates through the round
  summary.
