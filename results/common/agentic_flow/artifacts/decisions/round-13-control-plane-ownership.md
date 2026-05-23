# Decision: Round 13 Control-Plane Ownership Repair

The Humanize2 replay separates worker-owned artifacts from RLCR control-plane
files.

Worker-owned write sets may include code, tests, generated profile artifacts,
or `results/common/agentic_flow/**` when the worker is a capture worker. They
must not include `.humanize/rlcr/**`.

Coordinator-owned control-plane files:

- `.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md`

Codex-reviewer-owned control-plane files:

- `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-10-review-result.md`

Replay consequence:

- Worker prompts and contracts can read `.humanize/rlcr/**` as lineage input.
- Worker prompts, contracts, cartridge agent nodes, and `h2_primitives.yaml`
  worker `owned_write_set` entries cannot grant `.humanize/rlcr/**` write
  scope.
- Control-plane updates are represented by coordinator/reviewer events and this
  decision artifact.
