# Roadmap

This sequence separates the long-term product from the first evidence needed to build it. A phase is complete only when its observable exit condition is met; documentation or tests alone do not substitute for a named real-environment result.

## Phase 0 — Durable project memory

Status: **complete for this foundation task**

- Establish the repository entrypoint and canonical documents.
- Record accepted decisions, protected settings, non-goals, current non-implementation state, and next task.
- Self-verify that a new Codex session can recover the project intent without prior chat history.

Exit: all requested memory files and the 12-question report exist, and no application implementation has begun.

## Phase 0.5 — Public research baseline

Status: **complete**

- Commit the Phase 0 memory documents as an auditable baseline.
- Remove machine-specific paths and scan the publication set for secrets, personal/device data, raw logs, and proprietary artifacts.
- Create and push a public GitHub repository while accurately labeling the project as research/pre-implementation.
- Keep the project license provisional until ReboCap SDK redistribution terms are known.

Exit: the public `main` branch contains the safe Phase 0 baseline and does not imply that a working application exists.

## Phase 1 — Read-only ReboCap and VRChat interface discovery

Status: **documentation complete; live measurements remain gated**

- Verify the installed ReboCap version and locate authoritative SDK/API and license information.
- Characterize available skeleton data: joints, coordinates, units, timing, and connection lifecycle.
- Identify the least-invasive way to query and toggle only native SteamVR body-tracker output.
- Verify current official VRChat OSC tracker requirements and define the eventual real-surface acceptance check.
- Record evidence, failures, rejected paths, and unresolved questions.

Exit: an evidence-backed minimal input/output/control contract exists; no protected ReboCap setting has been changed merely for discovery.

Result: exit achieved for static/read-only discovery in `INTERFACE_CONTRACT.md`. The official input and VRChat wire contracts are known. A supported automatic native-output switch was not found, so that control portion remains a deliberate blocker rather than an assumed implementation detail.

## Phase 2 — Minimal retargeting specification and test data

Status: **in progress; limited live observation plus Phase 2A and Phase 2B offline gates are complete**

- A limited official-SDK Pose observation measured the 24-joint stream and cadence without retaining raw motion. It ended after a concurrent VRChat crash, so multi-client safety, known-action axes, reconnect, and shoulder-present/absent behavior remain unverified and live reconnection is not assumed safe.
- Phase 2A implemented pure/offline global-to-local conversion, motion-delta transfer, and target-skeleton FK. Thirty synthetic numeric tests prove straight, bent, compound, long/short, source-length-independent, mirrored, upper-body propagation, inheritance, non-identity-rest, and leg-control cases without any live-system access.
- Phase 2B confirmed all 24 parent relations from matching official Unity SDK v4 and Unreal Engine plugin v2 arrays, then replayed short hand-authored leg, root, Quaternion-boundary, and upper-body sequences through the same core. No recording format, interpolation layer, or external dependency was added.

- Leg Length and Thigh/Calf Balance now have explicit initial mathematical semantics. The other four morphology controls remain to be specified from controlled cases.
- Capture or construct the smallest lawful, non-personal pose samples needed to check straight legs, crouch, crossing, kick, weight shift, outstretched arms, and folded arms.
- Convert synthetic Target Skeleton world transforms into the planned VRChat tracker semantics entirely offline before returning to any live input or sending OSC.

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
