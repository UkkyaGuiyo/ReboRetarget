# Roadmap

This sequence separates the long-term product from the first evidence needed to build it. A phase is complete only when its observable exit condition is met; documentation or tests alone do not substitute for a named real-environment result.

## Phase 0 — Durable project memory

Status: **complete for this foundation task**

- Establish the repository entrypoint and canonical documents.
- Record accepted decisions, protected settings, non-goals, current non-implementation state, and next task.
- Self-verify that a new Codex session can recover the project intent without prior chat history.

Exit: all requested memory files and the 12-question report exist, and no application implementation has begun.

## Phase 1 — Read-only ReboCap and VRChat interface discovery

Status: **next**

- Verify the installed ReboCap version and locate authoritative SDK/API and license information.
- Characterize available skeleton data: joints, coordinates, units, timing, and connection lifecycle.
- Identify the least-invasive way to query and toggle only native SteamVR body-tracker output.
- Verify current official VRChat OSC tracker requirements and define the eventual real-surface acceptance check.
- Record evidence, failures, rejected paths, and unresolved questions.

Exit: an evidence-backed minimal input/output/control contract exists; no protected ReboCap setting has been changed merely for discovery.

## Phase 2 — Minimal retargeting specification and test data

Status: planned

- Define source-to-target skeleton semantics and coordinate transforms.
- Define the six initial manual morphology controls and their measurable effects.
- Capture or construct the smallest lawful, non-personal pose samples needed to check straight legs, crouch, crossing, kick, weight shift, outstretched arms, and folded arms.
- Select a minimal technology stack based on Phase 1 evidence.

Exit: solver inputs, outputs, invariants, and pose acceptance cases are explicit enough to implement without speculative infrastructure.

## Phase 3 — Retargeting core on controlled input

Status: planned

- Implement the smallest morphology-aware solver that preserves knee and shoulder information.
- Validate segment-balance controls using controlled or recorded poses before connecting live output.
- Measure processing time, jitter contribution, and stale-pose behavior.

Exit: controlled cases demonstrate target-skeleton reconstruction rather than uniform coordinate scaling.

## Phase 4 — Live ReboCap input and eight-point VRChat OSC output

Status: planned

- Connect the verified ReboCap input interface.
- Generate Hip, Chest, both Knees, both Feet, and both Upper Arms.
- Keep Quest controller hands on their normal route.
- Validate the actual VRChat avatar result, not only packets or upstream device registration.

Exit: the named poses are observably improved or accurately characterized in VRChat without stale-pose buildup.

## Phase 5 — Safe Native/Retarget switching and profiles

Status: planned

- Capture the exact pre-change native output state.
- Toggle only the verified conflicting ReboCap body output.
- Stop OSC and restore the exact prior state on OFF and normal exit.
- Add simple manual profile selection and persistence.
- Test originally-ON and originally-OFF states and controlled failure recovery.

Exit: switching is reversible and unrelated ReboCap settings remain unchanged.

## Phase 6 — Integrated user experience and resilience

Status: planned

- Decide, from verified platform capabilities, whether to use auto-start, window attachment, or another supported integration.
- Add ReboCap lifecycle watching, orderly shutdown, and best-effort crash restoration.
- Keep controls simple and expose only user-relevant morphology settings.

Exit: the normal workflow does not require repeatedly starting a separate app or manually editing ReboCap output settings.

## Phase 7 — Public-project readiness

Status: planned

- Select a license after checking ReboCap SDK and dependency compatibility.
- Add only necessary contribution, security, third-party notice, build, and release material.
- Scrub proprietary assets, personal/device identifiers, secrets, and raw logs.
- Document verified support and known limitations without claiming unfinished features.

Exit: a reproducible, legally reviewable repository is ready for an explicit publication decision. Publication itself requires user authorization.

## Independent future track — Quest Chest Yaw Anchor

Status: research only; **never a blocker for Phases 1–6**

Begin with OFF/MONITOR observation. AUTO correction may be considered only after reliable evidence, guardrails, and gradual correction behavior are demonstrated. See `QUEST_CHEST_YAW_ANCHOR.md`.
