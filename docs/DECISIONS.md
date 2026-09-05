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

### D-016 — Use the official WebSocket SDK as the input boundary

- Date: 2026-09-04
- Decision: The first input PoC connects to the ReboCap GUI broadcast through the official SDK, requests Unity-coordinate global rotations, and consumes pelvis translation plus the 24-joint quaternion pose.
- Why: This is the documented, least-invasive interface and supplies the rotation data needed to reconstruct a target skeleton.
- Boundary: The normal pose message does not provide a position for every bone. Timestamp semantics, live axes, hierarchy, multi-client behavior, and shoulder-tracker effects still require a controlled live validation.

### D-017 — Reject direct `config.data` rewriting for mode switching

- Date: 2026-09-04
- Decision: Do not implement ReboCap native-output control by rewriting the installed binary configuration store.
- Why: The candidate output fields share one custom/pickle-derived store with protected calibration, sensor, shoulder, AI, Ground IK, and skeleton settings; safe atomic query/set semantics and concurrent-write behavior are not established.
- Consequence: Automatic Native/Retarget switching remains blocked pending a supported control surface or a user-authorized, narrowly verified UI-automation fallback.

### D-018 — Keep eight OSC roles as a target, not an unconditional packet count

- Date: 2026-09-04
- Decision: Preserve Hip, Chest, both Knees, both Feet, and both Upper Arms as the target semantic set, but enable a point only after its absolute position and rotation are sufficiently accurate and stable in VRChat.
- Why: The set exactly matches the current VRChat maximum, while official documentation warns that inaccurate extra points can degrade IK and that fewer points may work better.
- Validation: Compare reduced lower-body sets with the full eight points on the actual avatar after FBT calibration.

### D-019 — Treat OSC slots as numbered transport slots, not authoritative roles

- Date: 2026-09-04
- Decision: ReboRetarget uses a stable internal slot order, but does not assume VRChat assigns a body role from the OSC slot number.
- Why: Current addresses are numbered; role interpretation occurs through tracker geometry and FBT calibration.

### D-020 — Keep the project license provisional

- Date: 2026-09-04
- Decision: Do not add a project LICENSE or redistribute ReboCap SDK files yet.
- Why: The inspected official SDK archives contain no SDK-level LICENSE/NOTICE/COPYING file or explicit redistribution grant. Referenced OSS licenses do not license the ReboCap SDK.

### D-021 — Transfer joint motion as local rotation deltas onto target rest transforms

- Date: 2026-09-04
- Decision: For the offline FK core, recover each source local rotation as `inverse(parent_global) * child_global`, remove the source rest-local rotation, apply the resulting motion delta after the target rest-local rotation, and run FK using only target rest-local vectors.
- Convention: Hamilton `(w,x,y,z)` active rotations; `left * right` applies `right` first and then `left`. Quaternion sign is not identity: `q` and `-q` are treated as the same rotation.
- Why: This preserves joint posture while allowing source and target bone lengths and rest rotations to differ. It also keeps a straight source knee straight instead of solving the target foot back to the source position.
- Boundary: Phase 2A proves this with synthetic coordinates only. Phase 2B confirms the 24-joint parent array from the official Unity SDK v4 and Unreal Engine plugin v2. Phase 2C implements the T-pose-delta composition as a pure offline adapter; installed ReboCap axis signs and live connection still require a separately authorized evidence gate before use.

### D-022 — Give leg controls total-length and fixed-total balance semantics

- Date: 2026-09-04
- Decision: `Leg Length` scales total thigh-plus-calf length. `Thigh / Calf Balance` shifts the thigh's share of that already-scaled total and transfers the same amount from the calf, preserving total length.
- Why: `Leg Length = 1.10` therefore means exactly 10% more total leg length, while Balance moves the target knee without also changing overall leg reach.
- Boundary: This is the initial synthetic-core meaning. User-facing ranges and avatar-specific defaults remain future work.

### D-023 — Adapt ReboCap T-pose deltas before the source-agnostic FK core

- Date: 2026-09-04
- Decision: Treat each official-SDK global Quaternion as a T-pose-relative delta and form the canonical source absolute rotation as `sdk_rotation_delta * source_bind_global_rotation` using the existing Hamilton `(w,x,y,z)` convention.
- Why: This matches the official Unity SDK v4 and Unreal Engine plugin v2 integration order and prevents a non-identity bind pose from being mistaken for identity world orientation.
- Boundary: The adapter is pure/offline and validates the confirmed 24-joint hierarchy. It does not connect to the SDK, resolve live axes, or modify the source-agnostic FK core.

### D-024 — Represent tracker placement as replaceable semantic local anchors

- Date: 2026-09-04
- Decision: Derive Hip, Chest, both Knees, both Feet, and both Upper Arms from a Target joint plus explicit local position and rotation offsets. Keep the semantic role independent from OSC slot/address assignment.
- Why: A physical tracker is mounted on a body surface or segment, not necessarily at a joint origin, and future calibration must be able to replace the initial placements without changing FK.
- Boundary: Phase 2C offsets are synthetic fixtures only. They are not product defaults or claims about the user's avatar, and no Euler, OSC packet, UDP sender, or live tracker is included.

### D-025 — Convert Quaternion to VRChat Euler only at the output boundary

- Date: 2026-09-05
- Decision: Keep Target Skeleton and semantic tracker rotations as Hamilton `(w,x,y,z)` active Quaternions. At the VRChat representation boundary only, convert to degree Euler values for fixed-world-axis `Z -> X -> Y` application; reconstruct the same rotation as `qY * qX * qZ` when validating.
- Why: Euler triples are non-unique and singular near X = +/-90 degrees. Rotation-equivalent Quaternion/matrix round trips prove the interface meaning without contaminating FK or treating one Euler triple as uniquely correct.
- Boundary: The output uses a deterministic finite branch but does not promise component-wise Euler continuity. No sender, scheduler, socket, or live input is part of this decision.

### D-026 — Keep body slots, head alignment, tracking-space alignment, and calibration separate

- Date: 2026-09-05
- Decision: Treat numbered body slots as configurable transport data, keep VRChat's fixed `head` alignment addresses outside the eight-role mapping, and model the local Source-to-VRChat tracking-space transform as one pure yaw-plus-translation rigid transform.
- Why: VRChat does not define numbered slots as semantic roles, head alignment is not a ninth body tracker, and one generic "calibration" concept would obscure different ownership and timing semantics.
- Boundary: ReboCap action calibration, VRChat FBT calibration, OSC head alignment, SteamVR playspace, and any future ReboRetarget recenter remain distinct. Phase 2D implements no recenter or live calibration behavior.

### D-027 — Gate live adapter validation on a natural Safe Point

- Date: 2026-09-05
- Decision: A live ReboCap adapter validation requires explicit user authorization after confirming a natural Safe Point: ReboCap is already running, VRChat and SteamVR are not running, and no active VR session exists. Codex may inspect state read-only but must not create the Safe Point by starting, stopping, or restarting anything. A Virtual Desktop background service alone is distinct from an active session; any ambiguity fails closed.
- Why: VRChat crashed during the earlier additional-SDK-client observation, and causality remains unresolved. The first controlled validation must minimize concurrent clients and preserve all user application state.
- Boundary: Start single-client-first. Multi-client support remains `UNVERIFIED` and requires separate opt-in approval. The protocol authorizes no OSC/UDP send, application or setting change, automatic reconnect, or Phase 2F body-motion execution.

### D-028 — Separate controlled input semantics from VRChat acceptance

- Date: 2026-09-05
- Decision: Phase 2F-A may validate known-motion semantics only after Phase 2E PASS, under its own explicit authorization and Safe Point. A Phase 2F-A PASS covers the controlled ReboCap-to-memory value path only; VRChat/FBT/avatar acceptance remains a later separately authorized gate.
- Why: Known input motion can test coordinate signs and transformation invariants without exposing an active VR session, while it cannot prove final avatar IK or tracker quality.
- Boundary: Use one single-client aggregate-only run of at most 60 seconds, no reconnect or OSC/VR contact, and do not infer sensor ownership, independent degrees of freedom, shoulder-tracker presence, anatomical correctness, or product suitability.

### Phase 2E run-specific override to D-027 (2026-09-05)

The user explicitly revised the retry Safe Point to require the same already-running ReboCap process, no VRChat, no SteamVR, and no ReboCap setting change. Existing Virtual Desktop Service/Streamer and their established TCP connection are permitted environmental variables; their presence alone must not block or fail this retry. No further Virtual Desktop termination or configuration operation is allowed. The override authorized one receive-only retry, now consumed; it grants no third connection, reconnect, OSC output, or Phase 2F-A execution. The retry was aborted without an aggregate result; see `PHASE_2E_RETRY_REPORT.md`.

### D-029 — Autonomous recovery with bounded standing permission

The historical D-027 one-run gate and run-specific override above are superseded for Phase 2E recovery by the user's `AUTONOMOUS_ENGINEERING_AUTHORITY.md`: useful offline recovery is autonomous; at most three sequential, changed-hypothesis Live attempts in one recorded cycle are permitted only after offline watchdog tests and the revised Safe Point. This is an accepted authority change, not a Phase 2E PASS. Protected settings, Virtual Desktop preservation, no output send, legal boundaries, and separately gated Phase 2F-A remain unchanged.

### D-030 — User-paced Phase 2F-A sessions

- Date: 2026-09-05
- Decision: The user authorized controlled known-motion validation, reported ordinary ReboCap Calibration complete, and approved one motion per supervised session of at most 60 total seconds with 20-second operator-response limits. This supersedes D-028's old single-run-all-cues boundary, not its receive-only/privacy restrictions.
- Boundary: Normal SDK close and owned-child exit are required before the next session. No overlapping clients or automatic reconnect loop. Virtual Desktop is intentionally untouched. ReboCap settings, Calibration, VR applications and all output sends remain out of scope. A timeout or ambiguous cue is not physical validation; report incomplete evidence rather than rushing the user.

### D-031 — Offline cue recovery and measured Python optimization

- Date: 2026-09-05
- Decision: Scheduled cue progression belongs in the bounded local controller, not chat or tool round trips. A scheduled marker and successful speech process are not human confirmation or proof of audibility. After offline recovery, obtain renewed explicit user readiness before the next controlled-motion session.
- Performance boundary: Preserve dynamic input validation, the eight-anchor/sixteen-message research encode/decode path, latest-only semantics and strict pure p99 **< 10 ms**. Record production-value timing separately from the heavier research probe; neither is physical sensor-to-avatar latency.
- Implementation boundary: Reuse exactly-unit immutable Quaternion values and one immutable prepared source bind; keep the defensive public adapter available. The research consumer uses a phase-preserving target cadence and skips missed deadlines rather than replaying old frames. Its configured frequency is a target, not a hard real-time minimum inter-start interval or a product guarantee. No global Windows timer-resolution or GC-policy change is authorized by this optimization.
- Evidence and remaining uncertainty: See `PERFORMANCE_INVESTIGATION_REPORT.md`. Historic Live timings cannot be retroactively diagnosed from a successful synthetic optimization. No native rewrite, dependency, framework, output sender or application operation is introduced.

### D-032 — Research before substantial new engineering

- Accepted: 2026-09-05, explicit user research-first directive.
- Decision: Before substantial new design/implementation, check official sources, GitHub source/examples/tests and relevant issues/PRs; verify freshness, target versions and licenses; compare existing knowledge to the hypothesis before the smallest local experiment. See `RESEARCH_FIRST_ENGINEERING.md` for the bounded gate and evidence record.
- Boundary: Learn from existing designs without wholesale architecture transplantation or unlicensed source copying. The gate reinforces rather than expands autonomous/Live/publication authority. This does not change current runtime code, acceptance thresholds or Phase 2F-A readiness requirements.

### D-033 — Preserve play; separate sampling research from capture

- Accepted: 2026-09-05, user's VRC-priority instruction and subsequent authorization for currently safe work.
- Decision: Continue useful offline work from existing evidence and synthetic data; do not add SDK clients, operate ReboCap/SteamVR/Virtual Desktop/Quest or overlap heavy benchmarks with play. Define coexistence safety separately; perform short labeled motion checks later outside play.
- Boundary: Discussing active sampling does not authorize recording or raw-data persistence. Standard recording compatibility, storage/retention permission and any concurrent SDK trial remain separate gates. Natural motion supplements but cannot replace physical-axis ground truth. See `PLAYTIME_SAMPLING_ASSESSMENT.md`.

## Open decisions

- Programming language, runtime, GUI toolkit, packaging, and supported Windows versions.
- ReboCap SDK redistribution terms and whether the binary may be bundled or must be user-supplied.
- The safe, observable mechanism for toggling only ReboCap's SteamVR body-tracker output, including exact state readback and crash recovery.
- Live ReboCap timestamp semantics, hierarchy/axis validation, multi-client support, shoulder-tracker differentiation, and observed rate/jitter.
- VRChat OSC alignment choice, duplicate-source behavior, stable point subset, and validated update rate on the real avatar.
- Which features define the first technical MVP versus the first user-facing v1, especially automatic startup/window attachment.
