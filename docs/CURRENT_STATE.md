# Current State

Last updated: 2026-09-04

## Current checkpoint

Phase 0.5, the read-only portion of Phase 1, a limited Phase 1.5 live-input observation, and the Phase 2A/2B pure-offline gates are complete. Phase 2B confirms all 24 ReboCap parent relations from matching official Unity SDK v4 and Unreal Engine plugin v2 arrays and replays short synthetic leg, root, Quaternion-boundary, and upper-body Pose sequences through the Phase 2A FK core. It has no external I/O and the combined suite passes 44 numeric tests. The earlier live run was stopped after a concurrent VRChat crash; causality between the additional SDK client and that crash remains unresolved.

## Actual implementation state

**No live or user-facing ReboRetarget application exists.** The repository now contains one small reusable pure/offline mathematics module, confirmed hierarchy metadata, in-memory synthetic sequence fixtures/tests, documentation, and the isolated research-only aggregate Pose Inspector. The mathematics module is not connected to ReboCap, VRChat, SteamVR, Virtual Desktop, Quest, OSC, or a GUI.

Not implemented:

- Product ReboCap SDK/API connection or live skeleton ingestion. A non-product research inspector exists under `research/` but is not used by the FK core.
- IK, foot locking/contact, smoothing, confidence weighting, or a production retargeting pipeline. Only pure rotation-delta transfer and FK exist.
- VRChat OSC tracker output.
- GUI, ReboCap-attached window, profiles, or persistence code.
- ReboCap watcher, automatic startup/shutdown, crash recovery, or setting restoration.
- SteamVR output control or UI automation.
- Quest chest-yaw monitoring or correction.
- Application builds, packages, releases, or deployment.

## Completed with evidence

- Phase 0 documentation baseline committed as `bc01e74` and pushed to `main`.
- Public repository: <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Installed ReboCap identified as `Release V02 Beta_02`; executable metadata also reports product version `0.48.0.0` and file version `1.0.0.0`.
- Official ReboCap WebSocket SDK archives and examples inspected outside the repository; no SDK archive or binary was committed.
- Skeleton contract identified as pelvis translation plus 24 SMPL-order quaternion rotations at a documented 60 Hz after action calibration.
- Installed ReboCap OpenVR driver, input profiles, configuration field names, and sanitized historical device-class evidence inspected read-only.
- Current official VRChat OSC addresses, port, coordinate/unit/rotation conventions, eight-point maximum, head alignment, and FBT calibration requirements verified.
- Minimal external boundary recorded in `INTERFACE_CONTRACT.md`.
- A research-only official-SDK Inspector received 29,233 valid 24-joint callbacks over 487.658 seconds at 59.9436 Hz average. Raw Pose frames saved: zero.
- Source timestamps were Unix seconds after wrapper conversion and remained monotonic. Receive p95/p99 intervals were 17.8/18.3 ms; 15 gaps of at least 50 ms, 64 sub-4 ms bursts, and 6 backlog-candidate runs justify latest-Pose processing.
- All 24 Quaternion streams were finite and normalized. Pelvis translation was finite. Shoulder-area and leg joints showed continuous activity, with duplicate-stat caveats for some adjacent joints.
- During observation, VRChat crashed in `UnityPlayer.dll` with access violation `0xc0000005`. No VRChat kill command was issued by the Inspector or Codex, but multi-client SDK causality is not proven either way. The Inspector was stopped immediately after the user raised the incident.
- A subsequent short relaunch failure was traced to a Watcher startup race. After the Watcher correction, VRChat remained running for more than 120 seconds without reconnecting the Inspector.
- `reboretarget/fk.py` now defines immutable Quaternion, Skeleton, Pose, Transform, and joint-diagnostic values plus pure global-to-local, target FK, retarget, and leg-control functions. It uses Python 3.10 standard-library mathematics only.
- Source-to-target transfer uses Hamilton `(w,x,y,z)` active rotations: `local = inverse(parent_global) * child_global`; `motion_delta = inverse(source_rest_local) * source_local`; `target_local = target_rest_local * motion_delta`.
- FK places each child at `parent_position + rotate(parent_global, target_rest_local_position)`. Source segment lengths and source joint positions are not copied.
- The original thirty Phase 2A synthetic `unittest` cases remain passing on Python 3.10, 3.11, and 3.13. They cover the confirmed 24-name order, strict 24-item input validation, Hamilton multiplication order, `q/-q` equivalence through the retarget path, identity and compound global-to-local recovery, non-identity rest rotations, T-pose/straight legs, 90-degree knee, 30-degree hip plus 45-degree knee, long/short target legs, source-length independence, left/right symmetry, parent-position propagation, Spine/Shoulder/Elbow propagation, numeric local-rotation diagnostics, determinism, validation, and Leg Length/Balance semantics.
- Straight source legs remained straight on 1.02 m and 0.70 m target legs; no IK or source-foot-position constraint was applied. A 0.52 m thigh plus 0.50 m calf with a 90-degree knee produced the expected knee `(−0.1, 0.48, 0)` and ankle `(−0.1, 0.48, −0.50)` in the synthetic fixture.
- Parent-inheritance diagnostics expose only the source local rotation and its numeric magnitude. The core deliberately has no inheritance classification Boolean or threshold, because a live near-zero value alone cannot distinguish anatomical zero motion from unavailable independent SDK data.
- `Leg Length` scales total upper-plus-lower leg length exactly. `Thigh / Calf Balance` transfers a share of that fixed total between the two segments.
- The official normalized parent-index array is `(-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19,20,21)`. All 24 relations are marked `CONFIRMED` from matching Unity SDK v4 and Unreal Engine plugin v2 code, with public source references and archive hashes retained as metadata.
- A seven-frame straight-to-bend sequence preserved analytic Knee/Ankle positions and 5-degree Hip plus 10-degree Knee frame steps. Long 1.02 m and short 0.70 m targets kept identical local joint rotations while using their own segment lengths.
- Four synthetic root frames propagated lateral, vertical, and forward/back translation exactly to every joint. A four-frame sign/boundary case produced shortest rotation steps `0, 2, 0` degrees across `q/-q` and `179 -> 181`.
- A five-frame Spine3/Collar/Shoulder/Elbow sequence used the same FK core. A fixture-only `Shoulder Width = 1.10` changed the shoulder span from 0.40 m to 0.44 m without changing the 0.28 m upper-arm or 0.25 m forearm fixture lengths. Product Arm Length remains deferred.
- The official SDK describes rotations as relative to T-pose, and official Unity/Unreal integration code composes them with bind/T-pose global rotations. No live adapter implementing that semantic boundary exists yet.

## Verified repository facts

- Branch is `main`, tracking `origin/main`.
- `origin` is the public GitHub repository above.
- No LICENSE exists. The official downloadable ReboCap SDK archives inspected on 2026-09-04 contained no SDK-level license or redistribution grant, so project licensing remains provisional.
- Publication safety scans found no local user paths, private keys/tokens, email addresses, device identifiers, proprietary binaries, or raw logs in committed content.
- Phase 1.5 observed an already-running ReboCap/SteamVR/Virtual Desktop/VRChat environment. The Inspector did not change their settings or send OSC. Later Watcher repair and VRChat restart were separately authorized recovery work, not part of the read-only observation.

## Go / No-Go

- **GO:** the next minimal offline gate: derive the planned Hip, Chest, Knee, Foot, and Upper Arm tracker transforms from synthetic Target Skeleton world transforms without sending them.
- **NO-GO:** live SDK reconnection, OSC output, Two Bone IK, production retargeting, Watcher integration, chest-yaw correction, and automatic Native/Retarget switching. Live multi-client safety, real axis signs, the safe ReboCap native-output control surface, and real VRChat acceptance behavior are not yet proven.

## Single recommended next task

Create the smallest pure/offline Target-Skeleton-to-tracker transform PoC for the planned eight semantic points. Use only synthetic Target poses, make offsets/orientations explicit, and verify deterministic transforms and left/right symmetry. Do not add OSC transport, a live ReboCap adapter, IK, VR application access, or personal raw motion.

Use the priority order in D-011. If a live VR session is active, use quiet/read-only inspection and do not foreground, restart, stop, reset, or change ReboCap/SteamVR/VRChat/Virtual Desktop/Quest state without explicit authorization.

## Blockers and unverified items

- ReboCap SDK redistribution permission is unconfirmed.
- The exact safe query/set/restore control surface for ReboCap's native SteamVR body output is unknown.
- Quaternion validity, joint count, Pelvis translation, timestamp unit, and cadence were live-observed. Parent hierarchy is now confirmed from official code, while axis signs against known actions, safe multi-client support, and the physical shoulder-tracker effect versus a no-shoulder A/B remain unverified.
- VRChat crashed during the live observation. The crash signature is known, and no kill command was issued, but causality involving the additional SDK client remains unresolved.
- Receive gaps/bursts and six backlog candidates require latest-Pose semantics. Their exact SDK-versus-client scheduling origin remains unresolved.
- External disconnect/reconnect and stale-frame recovery were not exercised; the recorded disconnect was Inspector shutdown.
- VRChat OSC behavior has been verified from current official documentation, but not yet on the user's actual VRChat avatar/environment.
- Duplicate-role precedence between native SteamVR and OSC sources is not documented sufficiently to rely on.
- Python 3.10 plus the standard library is proven for the Phase 2A math PoC; the product technology stack and MVP/v1 boundary are not selected.
- The official hierarchy is confirmed, but the SDK's T-pose-relative global rotations still require an explicit adapter before the offline core can consume live values correctly.
- Upper-body joints fit the generic FK structure, but duplicate live statistics do not yet say which Shoulder/Elbow/Wrist/Hand or Ankle/Foot nodes have independent trustworthy rotation versus inherited/helper behavior.
- Actual avatar rest skeleton extraction, coordinate alignment, tracker-transform offsets, and the remaining Hip/Arm morphology-control meanings are not implemented. Shoulder Width exists only as a synthetic fixture parameter.
- Crash-safe restoration behavior has not been designed or tested.
- The Quest chest-yaw signal source, quality, drift model, and usefulness are unverified.

## Repository state at handoff

- Branch: `main`.
- Phase 0 baseline: `bc01e74` (`docs: establish ReboRetarget project memory`).
- Remote/GitHub publication: public `origin/main` at <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Phase 1.5 research commit: `35b3308`.
- Phase 2A commit `1731c9d` is published on `origin/main`.
- Phase 2B source, synthetic tests, and documentation are pending a separate review/commit at this handoff.
- Deployment: none.
