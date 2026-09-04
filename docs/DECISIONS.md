# Decisions

Status terms: **Accepted** is binding until explicitly superseded; **Open** is not yet a decision.

## Accepted decisions

### D-001 — Use morphology retargeting, not a uniform tracker scale

- Date: 2026-09-04
- Decision: Reconstruct human joint motion on a target skeleton with different proportions.
- Why: Independent differences in legs, hips, shoulders, upper arms, and forearms cannot be corrected by one coordinate multiplier.

### D-002 — Plan eight VRChat OSC tracker outputs

- Date: 2026-09-04
- Decision: Target Hip, Chest, Left Knee, Right Knee, Left Foot, Right Foot, Left Upper Arm, and Right Upper Arm.
- Why: This set carries the intended lower- and upper-body constraints while the hands remain on their normal controller path.

### D-003 — Keep both knee trackers

- Date: 2026-09-04
- Decision: Do not reduce the lower body to hip plus feet and leave all knee behavior to VRChat IK.
- Why: ReboCap's knee motion is needed to preserve dance, leg crossing, kicks, inward/outward knee motion, crouching, and one-leg weight shifts.

### D-004 — Keep ReboCap shoulder tracking as solver input

- Date: 2026-09-04
- Decision: Use available Collar, Shoulder, UpperArm, Elbow, Forearm, Wrist, and related upper-body data to solve the final Chest and Upper Arm tracker outputs. Do not discard shoulder tracking merely because VRChat has no independent shoulder tracker slot.
- Why: The user's shoulder trackers materially improve arm motion.

### D-005 — Preserve the normal hand route in the initial version

- Date: 2026-09-04
- Decision: Quest 3 controllers continue through the normal SteamVR-to-VRChat route. Virtual controllers are outside the initial scope.
- Why: The project can improve body morphology without replacing a working hand-input path.
- Boundary: Mesh-surface differences, such as hands intersecting an extremely large chest, are not an initial target.

### D-006 — Use simple manual morphology controls first

- Date: 2026-09-04
- Decision: Do not automatically analyze avatar skeletons in the initial version. Let the user adjust while looking in the VRChat mirror.
- Initial candidates: Leg Length, Thigh/Calf Balance, Hip Width, Arm Length, UpperArm/Forearm Balance, and Shoulder Width.
- Why: The internal model may be advanced, but initial interaction should remain understandable and testable.

### D-007 — Save per-avatar profiles with manual selection

- Date: 2026-09-04
- Decision: Store settings in profiles; automatic avatar detection is not required initially.
- Why: Manual selection is sufficient for an initial usable workflow and avoids premature integration.

### D-008 — Integrate around ReboCap rather than modifying it by default

- Date: 2026-09-04
- Decision: Aim for automatic startup, connection, and an attached/adjacent ReboCap-like UI experience. Prefer official extension points or an external window over changing ReboCap itself.
- Why: The desired experience is one coherent workflow, not necessarily an invasive product modification.

### D-009 — Native/Retarget switching must be automatic and reversible

- Date: 2026-09-04
- Decision:
  - Native: ReboCap → its normal SteamVR virtual body trackers → VRChat.
  - Retarget ON: remember the exact prior native-output state; stop only the conflicting ReboCap SteamVR body-tracker output; ReboCap Skeleton → ReboRetarget → VRChat OSC eight points.
  - Retarget OFF: stop ReboRetarget OSC; restore the exact state captured before the change.
- Why: The user should not repeatedly edit ReboCap settings, and an originally OFF setting must never be assumed to have been ON.

### D-010 — Protect unrelated ReboCap settings

- Date: 2026-09-04
- Decision: Do not change shoulder tracker assignment, sensor assignment, AI Engine, 6-axis/magnetic settings, Ground IK, skeleton settings, native calibration, or other user-tuned items during mode switching.
- Why: Only the minimum setting needed to avoid duplicate body output belongs to this feature. The exact switch has not yet been identified and must be researched in the real environment.

### D-011 — Use a least-invasive interoperability research order

- Date: 2026-09-04
- Decision: Prefer (1) official SDK/API, (2) configuration file, (3) local IPC/API, (4) Windows UI Automation, then (5) internal analysis/hooking only if necessary.
- Why: Supported or observable interfaces are safer and more maintainable.
- Boundary: Research is for interoperability only. Do not bypass authentication, payment, or licensing, and do not publish proprietary code or binaries.

### D-012 — Treat Quest chest yaw as independent future research

- Date: 2026-09-04
- Decision: ReboCap remains the normal full-body source. Quest IOBT chest yaw may become only a slow external yaw reference, beginning with OFF and MONITOR modes before any AUTO mode.
- Why: It may detect/correct long-duration yaw drift, but unstable Quest data must not disturb working tracking or block the MVP.

### D-013 — Prefer fresh poses and avoid duplicate smoothing

- Date: 2026-09-04
- Decision: Design for low latency and jitter around an expected roughly 60 Hz input. If behind, discard stale work in favor of the latest pose, and avoid smoothing the same motion in multiple layers.
- Why: Delayed replay is worse than dropping obsolete poses for live embodiment.

### D-014 — Avoid speculative infrastructure

- Date: 2026-09-04
- Decision: Do not prebuild a plugin system, DI container, event bus, database, excessive repository abstraction, custom SteamVR driver, or unnecessary communication layer.
- Why: Add infrastructure only when a verified current requirement needs it; retain only modest responsibility separation.

### D-015 — Keep public claims and repository contents honest

- Date: 2026-09-04
- Decision: Public documentation must say what is research, prototype, working, or missing. Do not commit proprietary third-party assets, personal/device data, secrets, or raw logs. Confirm license compatibility before publication.
- Why: The intended project is public and useful to other ReboCap/VRChat users without misrepresentation or redistribution risk.

## Open decisions

- Programming language, runtime, GUI toolkit, packaging, and supported Windows versions.
- Exact ReboCap SDK/API version, redistribution terms, skeleton schema, coordinate system, and connection lifecycle.
- The safe, observable mechanism for toggling only ReboCap's SteamVR body-tracker output.
- Exact VRChat OSC endpoints, coordinate conventions, tracker activation/calibration behavior, and validated update rate.
- Which features define the first technical MVP versus the first user-facing v1, especially automatic startup/window attachment.
