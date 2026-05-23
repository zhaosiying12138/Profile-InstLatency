# Worker Round 5 Candidate-Simulator Output

Round: 5
Worker: Anscombe
Capture type: normalized reconstruction
Status: reviewed and accepted for candidate-simulator scope
Commit: `773f27d67e8306ec8fbafc434dcd158953e71e95`

## Work Completed

- Added T20 peer-side observation mirroring in `scripts/search_model.py` so an
  instruction row that only appears as a T20 pair peer can still receive the
  corresponding startup-slope constraints when that row exists.
- Added a T12 trailing minimum-residual plateau guard so short clean-prefix
  sweeps do not render exact latency without enough no-stall post-transition
  coverage.
- Added focused tests for peer-only T20 rows and the K0/K1 T12 short-sweep
  overclaim case.
- Regenerated real-platform search, field-status, inventory, quality, summary,
  and affected sidecar artifacts.

## Files Changed by Commit 773f27d6

- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`

## Review Outcome

Round 5 review accepted the candidate-simulator code fixes:

- Peer-side T20 mirroring is implemented.
- `vredsum_vs` has peer-side T20 groups in the regenerated real-platform search
  artifact.
- The T12 K0/K1 short-sweep overclaim is covered by a regression test.
- The reviewer reproduced real-platform search regeneration against the
  checked-in JSON.

Round 5 review did not mark the full workflow complete. AC-12 and AC-13 were
partial before this capture package because the code worker's Humanize2
artifacts were missing. AC-16 remained blocked by absent machine-readable human
approval and by unresolved `non_identifiable` risk handling that was later
hardened in Round 6.

## Historical Round 5 Artifact Hashes After Commit 773f27d6

- `results/common/real_platform_inventory.json`:
  `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d`
- `results/common/real_platform_field_status.json`:
  `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
- `results/common/search_model_real_platform.json`:
  `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
- `results/common/experiment_quality.md`:
  `6062c76f6f051eac6c60b0ead3be0e8ac74bc3f723841a0ec19d0d7a750e7307`

## Remaining Items

- AC-16 remains fail-closed because the real-platform report has
  `Gate status: NOT_READY`, confidence is `awaiting_human_approval`, and no
  machine-readable approval artifact exists.
- The 39 `non_identifiable` rows still require stronger evidence/modeling or
  explicit human risk acceptance tied to current artifact hashes.
- Round 6 approval-gate hardening is recorded separately in the Gibbs capture
  package.

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: The Round 6 task selected `LESSON_IDS: NONE`.
