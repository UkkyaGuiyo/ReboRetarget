# Current State

Last updated: 2026-09-04

## Current checkpoint

Phase 0.5 and the read-only portion of Phase 1 are complete. The project-memory baseline is committed and published in a public GitHub repository. The installed ReboCap/SteamVR surfaces, current official ReboCap SDK contract, current VRChat OSC tracker contract, relevant OSS, license uncertainty, and the minimum pre-implementation interface boundary are documented.

## Actual implementation state

**No ReboRetarget application implementation exists.** The repository still contains documentation only.

Not implemented:

- ReboCap SDK/API connection or skeleton ingestion.
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

## Verified repository facts

- Branch is `main`, tracking `origin/main`.
- `origin` is the public GitHub repository above.
- No LICENSE exists. The official downloadable ReboCap SDK archives inspected on 2026-09-04 contained no SDK-level license or redistribution grant, so project licensing remains provisional.
- Publication safety scans found no local user paths, private keys/tokens, email addresses, device identifiers, proprietary binaries, or raw logs in committed content.
- ReboCap, SteamVR, and VRChat were not running during the read-only inspection. Virtual Desktop was running and was not foregrounded, restarted, stopped, reset, or reconfigured.

## Go / No-Go

- **GO:** a minimal, research-only live Pose inspector using the official SDK, in a user-authorized calibrated ReboCap session. It should verify callback data, timing, axes, hierarchy, reconnect, and shoulder behavior and should not send OSC.
- **NO-GO:** production retargeting, production OSC, and automatic Native/Retarget switching. The safe ReboCap native-output control surface and real VRChat acceptance behavior are not yet proven.

## Single recommended next task

Build the smallest disposable/read-only Pose inspector around the official SDK and run it only at an agreed safe point with ReboCap already calibrated. Capture aggregate timing and explicit known-pose checks; do not record personal motion, modify settings, start a solver, or send VRChat OSC.

Use the priority order in D-011. If a live VR session is active, use quiet/read-only inspection and do not foreground, restart, stop, reset, or change ReboCap/SteamVR/VRChat/Virtual Desktop/Quest state without explicit authorization.

## Blockers and unverified items

- ReboCap SDK redistribution permission is unconfirmed.
- The exact safe query/set/restore control surface for ReboCap's native SteamVR body output is unknown.
- Current installed-build pose data, timestamp meaning, axes, hierarchy, multi-client support, and physical shoulder-tracker effect have not been live-tested.
- VRChat OSC behavior has been verified from current official documentation, but not yet on the user's actual VRChat avatar/environment.
- Duplicate-role precedence between native SteamVR and OSC sources is not documented sufficiently to rely on.
- Technology stack and MVP/v1 boundary are not selected.
- Crash-safe restoration behavior has not been designed or tested.
- The Quest chest-yaw signal source, quality, drift model, and usefulness are unverified.

## Repository state at handoff

- Branch: `main`.
- Phase 0 baseline: `bc01e74` (`docs: establish ReboRetarget project memory`).
- Remote/GitHub publication: public `origin/main` at <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Expected dirty files after final handoff: none.
- Deployment: none.
