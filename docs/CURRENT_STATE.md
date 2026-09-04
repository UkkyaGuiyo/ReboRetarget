# Current State

Last updated: 2026-09-05

## Current checkpoint

Phase 0.5, the read-only portion of Phase 1, a limited Phase 1.5 live-input observation, and the Phase 2A/2B/2C/2D pure-offline gates are complete. Phase 2D maps the eight Phase 2C semantic Quaternion transforms to configurable numbered slots, converts rotation at the output boundary to VRChat's degree Euler convention, represents separate head alignment and tracking-space alignment, and encodes/decodes the needed OSC 1.0 message subset only in memory. It has no external I/O and the combined suite passes 83 tests. The earlier live run was stopped after a concurrent VRChat crash; causality between the additional SDK client and that crash remains unresolved.

## Actual implementation state

**No live or user-facing ReboRetarget application exists.** The repository contains a small pure/offline FK core, a separate ReboCap-delta value adapter, an eight-role semantic tracker-anchor builder, a network-free VRChat OSC representation/codec layer, confirmed hierarchy metadata, in-memory synthetic fixtures/tests, documentation, and the isolated research-only aggregate Pose Inspector. None is connected to ReboCap, VRChat, SteamVR, Virtual Desktop, Quest, or a GUI; the OSC codec only transforms values to and from bytes in memory.

Not implemented:

- Product ReboCap SDK/API connection or live skeleton ingestion. The pure adapter accepts already-constructed values only; a non-product research inspector exists under `research/` but is not used by the FK core.
- IK, foot locking/contact, smoothing, confidence weighting, or a production retargeting pipeline. Only pure rotation-delta transfer and FK exist.
- UDP transport, OSC transmission, timing/scheduling, or actual tracker output. Offline slot mapping, Euler conversion, and minimal packet encoding/decoding are implemented.
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
- `reboretarget/rebocap_adapter.py` implements that semantic boundary offline as `source_absolute_global = sdk_rotation_delta * source_bind_global_rotation`, validates the confirmed 24-joint hierarchy/count, and passes Pelvis translation through exactly. Noncommuting tests reject the reverse multiplication order.
- `reboretarget/tracker_anchors.py` generates exactly eight immutable Hip, Chest, Knee, Foot, and Upper Arm semantic transforms from Target Pose joints plus replaceable local position/rotation offsets. It contains no OSC address or slot.
- Identity, long/short legs, knee bend, root translation, body yaw, Shoulder Width, fixture Hip Width, mirror symmetry, noncommuting rotation offset, validation, and full SDK-delta-to-Target-to-eight-anchor integration are covered by 17 new tests. Together with the original 44, all 61 tests pass on Python 3.10, 3.11, and 3.13.
- The synthetic Upper Arm anchor uses the midpoint of Shoulder-to-Elbow; Foot uses the midpoint of the Target Ankle-to-Foot rest vector from Ankle; Chest uses Spine3 plus an offset. These are test fixtures, not product defaults.
- `reboretarget/vrchat_osc.py` keeps semantic roles separate from replaceable slot mappings and validates all eight roles and slots exactly once. The default internal order is Hip, Chest, both Knees, both Feet, and both Upper Arms in slots 1 through 8; it is not a VRChat role definition.
- Target positions pass through unchanged as metre-valued Unity-axis coordinates at this boundary. Installed live ReboCap axis signs and origin remain unverified, so this is a synthetic/offline result rather than a live coordinate proof.
- Tracker Quaternion conversion uses degree Euler values for fixed-world-axis `Z -> X -> Y` application. Reconstruction is `qY * qX * qZ`; identity, single-axis, compound, 89.9/90/90.1-degree, 179/180/181/-179-degree, and `q/-q` round trips are finite and rotation-equivalent.
- The minimal OSC 1.0 codec supports only the required address, exact `,fff` type tag, NUL termination, four-byte alignment, and three big-endian float32 values. Strict in-memory decode rejects malformed padding, tags, lengths, addresses, and non-finite values.
- One Phase 2C synthetic pipeline produces eight slot poses and sixteen unique position/rotation messages, all decoded in memory. No socket or network sender exists.
- Head position/rotation values use separate fixed addresses and never enter the eight body slots. A separate yaw-plus-translation rigid transform applies uniformly to all eight trackers and preserves pairwise distance and relative rotation; no recenter is implemented.
- Phase 2D adds 22 tests to the prior 61 for 83 passing standard-library tests on Python 3.10, 3.11, and 3.13.

## Verified repository facts

- Branch is `main`, tracking `origin/main`.
- `origin` is the public GitHub repository above.
- No LICENSE exists. The official downloadable ReboCap SDK archives inspected on 2026-09-04 contained no SDK-level license or redistribution grant, so project licensing remains provisional.
- Publication safety scans found no local user paths, private keys/tokens, email addresses, device identifiers, proprietary binaries, or raw logs in committed content.
- Phase 1.5 observed an already-running ReboCap/SteamVR/Virtual Desktop/VRChat environment. The Inspector did not change their settings or send OSC. Later Watcher repair and VRChat restart were separately authorized recovery work, not part of the read-only observation.

## Go / No-Go

- **CONDITIONAL GO:** design the next Live ReboCap Adapter Safety Validation as a separate, explicitly authorized procedure covering SDK single/multi-client conditions, live delta adaptation, latest-pose behavior near 60 Hz, and disconnect invalidation, while still sending no VRChat OSC.
- **NO-GO:** starting that live procedure without a safe point and explicit authorization; UDP/OSC output; VRChat, SteamVR, Virtual Desktop, or Quest interaction; Two Bone IK; production retargeting; Watcher integration; chest-yaw correction; and automatic Native/Retarget switching. Live multi-client safety, real axis signs, the safe ReboCap native-output control surface, and real VRChat acceptance behavior are not yet proven.

## Single recommended next task

Design the smallest separate Phase 2E Live ReboCap Adapter Safety Validation procedure. It must resolve SDK single/multi-client conditions and protect an active VR session before any connection is attempted; then validate live delta adaptation, latest-pose behavior near 60 Hz, and disconnect invalidation without sending VRChat OSC. Do not start or touch ReboCap, VRChat, SteamVR, Virtual Desktop, or Quest until the user explicitly authorizes a safe point.

Use the priority order in D-011. If a live VR session is active, use quiet/read-only inspection and do not foreground, restart, stop, reset, or change ReboCap/SteamVR/VRChat/Virtual Desktop/Quest state without explicit authorization.

## Blockers and unverified items

- ReboCap SDK redistribution permission is unconfirmed.
- The exact safe query/set/restore control surface for ReboCap's native SteamVR body output is unknown.
- Quaternion validity, joint count, Pelvis translation, timestamp unit, and cadence were live-observed. Parent hierarchy is now confirmed from official code, while axis signs against known actions, safe multi-client support, and the physical shoulder-tracker effect versus a no-shoulder A/B remain unverified.
- VRChat crashed during the live observation. The crash signature is known, and no kill command was issued, but causality involving the additional SDK client remains unresolved.
- Receive gaps/bursts and six backlog candidates require latest-Pose semantics. Their exact SDK-versus-client scheduling origin remains unresolved.
- External disconnect/reconnect and stale-frame recovery were not exercised; the recorded disconnect was Inspector shutdown.
- VRChat OSC behavior has been verified from current official documentation, but not yet on the user's actual VRChat avatar/environment.
- Current release notes add a single-pulse head-position snap, while the main tracker page does not specify head-position streaming thresholds. Do not apply the documented head-rotation 300 ms/10-second rules to head position by inference.
- Duplicate-role precedence between native SteamVR and OSC sources is not documented sufficiently to rely on.
- Python 3.10, 3.11, and 3.13 plus the standard library are proven for the offline test suite; the product technology stack and MVP/v1 boundary are not selected.
- The official hierarchy and offline T-pose-delta adapter are implemented, but known-action live axes and safe live SDK ingestion remain unverified.
- Upper-body joints fit the generic FK structure, but duplicate live statistics do not yet say which Shoulder/Elbow/Wrist/Hand or Ankle/Foot nodes have independent trustworthy rotation versus inherited/helper behavior.
- Actual avatar rest skeleton extraction, coordinate alignment, calibrated tracker-transform offsets, and the remaining Arm morphology-control meanings are not implemented. Shoulder Width and Hip Width exist only as synthetic fixture parameters.
- Crash-safe restoration behavior has not been designed or tested.
- The Quest chest-yaw signal source, quality, drift model, and usefulness are unverified.

## Repository state at handoff

- Branch: `main`.
- Phase 0 baseline: `bc01e74` (`docs: establish ReboRetarget project memory`).
- Remote/GitHub publication: public `origin/main` at <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Phase 1.5 research commit: `35b3308`.
- Phase 2A commit `1731c9d` is published on `origin/main`.
- Phase 2B commit `54c6dc7` is published on `origin/main`.
- Phase 2C commit `07d525b` is published on `origin/main`.
- Phase 2D source, synthetic tests, and documentation are pending Scope Guard review and a separate commit at this handoff.
- Deployment: none.
