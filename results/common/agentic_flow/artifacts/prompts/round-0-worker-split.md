# Prompt Capture: Round 0 Worker Split

Prompt ID: round-0-worker-split
Task owner: RLCR coordinator
Target files/directories: disjoint worker-owned scopes from `docs/plan.md`
Allowed write scope: worker-specific paths only
Required inputs: `docs/plan.md`, `.humanize/bitlesson.md`, current git status
Expected artifacts: worker outputs, verification commands, risks, and changed paths
Model and reasoning effort requested: gpt-5.5:xhigh where available
Timeout assumptions: per-worker short implementation slice
Success criteria: workers return owned-file changes without editing RLCR state or `docs/plan.md`

Round 0 worker packages:

- Worker A: LLVM read-only extractor and mapping docs.
- Worker B: gem5 RVV kill-check assembly and runner.
- Worker C: timestamp marker implementation and trace schema.
- Worker D: assembly generator and template metadata.
- Worker E: analyzer, fitting, parameter search, calibration gate, LLVM helper, and capture scaffold.
- Worker F: results schema validation and report generation.
- Worker G: Humanize2 primitive capture, cartridge draft, and replay documentation.
- Worker H: gated LLVM 22.1.3 YuShuXin schedule-model implementation and LLVM tests.
