# Current State

Last updated: 2026-09-04

## Current checkpoint

Phase 0.5, the read-only portion of Phase 1, and a limited Phase 1.5 live-input observation are complete. The project-memory baseline is committed and published in a public GitHub repository. Static interface research is documented, and the Phase 1.5 run measured the current official-SDK stream without retaining raw motion. The run was stopped after a concurrent VRChat crash; causality between the additional SDK client and that crash is unresolved.

## Actual implementation state

**No ReboRetarget application implementation exists.** The repository contains documentation plus one isolated research-only aggregate Pose inspector; it does not contain a retargeter or output path.

Not implemented:

- Product ReboCap SDK/API connection or skeleton ingestion. A non-product research inspector exists under `research/`.
- Retargeting mathematics or solver.
- VRChat OSC tracker output.
- GUI, ReboCap-attached window, profiles, or persistence code.
- ReboCap watcher, automatic startup/shutdown, crash recovery, or setting restoration.
- SteamVR output control or UI automation.
- Quest chest-yaw monitoring or correction.
- Tests, builds, packages, releases, or deployment.

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

## Verified repository facts

- Branch is `main`, tracking `origin/main`.
- `origin` is the public GitHub repository above.
- No LICENSE exists. The official downloadable ReboCap SDK archives inspected on 2026-09-04 contained no SDK-level license or redistribution grant, so project licensing remains provisional.
- Publication safety scans found no local user paths, private keys/tokens, email addresses, device identifiers, proprietary binaries, or raw logs in committed content.
- Phase 1.5 observed an already-running ReboCap/SteamVR/Virtual Desktop/VRChat environment. The Inspector did not change their settings or send OSC. Later Watcher repair and VRChat restart were separately authorized recovery work, not part of the read-only observation.

## Go / No-Go

- **CONDITIONAL GO:** a pure/offline Target Skeleton FK transform PoC using synthetic fixtures and no external output. The live stream is sufficient to justify transform work, but live multi-client safety and axis checks remain gates for reconnecting the Inspector.
- **NO-GO:** OSC output, Two Bone IK, production retargeting, Watcher integration, chest-yaw correction, and automatic Native/Retarget switching. The safe ReboCap native-output control surface and real VRChat acceptance behavior are not yet proven.

## Single recommended next task

Build the smallest pure/offline Target Skeleton FK transform PoC: map the confirmed 24 global rotations plus Pelvis translation onto one fixed target hierarchy, starting from synthetic T-pose and known-rotation fixtures. Do not connect to live ReboCap, send OSC, add IK, alter SteamVR output, or integrate a Watcher in this step.

Use the priority order in D-011. If a live VR session is active, use quiet/read-only inspection and do not foreground, restart, stop, reset, or change ReboCap/SteamVR/VRChat/Virtual Desktop/Quest state without explicit authorization.

## Blockers and unverified items

- ReboCap SDK redistribution permission is unconfirmed.
- The exact safe query/set/restore control surface for ReboCap's native SteamVR body output is unknown.
- Quaternion validity, joint count, Pelvis translation, timestamp unit, and cadence were live-observed. Axis signs against known actions, hierarchy/local rotations, safe multi-client support, and the physical shoulder-tracker effect versus a no-shoulder A/B remain unverified.
- VRChat crashed during the live observation. The crash signature is known, and no kill command was issued, but causality involving the additional SDK client remains unresolved.
- Receive gaps/bursts and six backlog candidates require latest-Pose semantics. Their exact SDK-versus-client scheduling origin remains unresolved.
- External disconnect/reconnect and stale-frame recovery were not exercised; the recorded disconnect was Inspector shutdown.
- VRChat OSC behavior has been verified from current official documentation, but not yet on the user's actual VRChat avatar/environment.
- Duplicate-role precedence between native SteamVR and OSC sources is not documented sufficiently to rely on.
- Technology stack and MVP/v1 boundary are not selected.
- Crash-safe restoration behavior has not been designed or tested.
- The Quest chest-yaw signal source, quality, drift model, and usefulness are unverified.

## Repository state at handoff

- Branch: `main`.
- Phase 0 baseline: `bc01e74` (`docs: establish ReboRetarget project memory`).
- Remote/GitHub publication: public `origin/main` at <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Expected dirty files before the Phase 1.5 commit: the isolated research inspector and the three Phase 1.5 documentation updates.
- Deployment: none.
