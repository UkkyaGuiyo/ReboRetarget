# ReboRetarget

ReboRetarget is a planned real-time morphology-retargeting tool for adapting ReboCap body motion to VRChat avatars with different skeletal proportions.

## Status

Research and offline-core stage. Phase 1 mapped the installed ReboCap/SteamVR surfaces and the current VRChat OSC tracker protocol. Phase 2A added a standard-library-only, pure/offline target-skeleton FK core. Phase 2B confirmed the official 24-joint parent hierarchy and validated short synthetic Pose sequences. Phase 2C adds a pure ReboCap T-pose-delta adapter and derives eight semantic tracker transforms from synthetic Target poses. No live application, SDK client, OSC sender, IK, GUI, watcher, or SteamVR control has been implemented.

The intended primary environment is Meta Quest 3 + Virtual Desktop + SteamVR + VRChat + ReboCap. The initial direction preserves Quest controller hand tracking while generating eight planned VRChat OSC tracker outputs from the ReboCap skeleton and manually tuned avatar profiles.

Start with [AGENTS.md](AGENTS.md), then read the canonical documents under [`docs/`](docs/). The implementation boundary is summarized in [`docs/INTERFACE_CONTRACT.md`](docs/INTERFACE_CONTRACT.md).

## Why morphology retargeting?

A single tracker scale cannot correct different thigh/calf, upper-arm/forearm, hip, and shoulder proportions. ReboRetarget is intended to reconstruct captured joint motion on the target avatar skeleton so that straight legs, crossed legs, kicks, crouches, weight shifts, folded arms, and other poses retain their intent.

## Publication and license status

This repository is public at <https://github.com/UkkyaGuiyo/ReboRetarget>. It contains research documentation, the isolated Phase 1.5 aggregate Inspector, and pure/offline retarget, sequence, ReboCap-delta-adapter, and tracker-anchor mathematics with synthetic tests. It does not contain ReboCap SDK files, proprietary binaries, raw logs, personal motion data, or device identifiers.

No project license has been selected. The downloadable ReboCap SDK archives inspected during Phase 1 did not contain an SDK-level license or redistribution grant. Project licensing therefore remains provisional until the vendor terms and all future dependencies are confirmed. No third-party code is licensed merely by being described or linked here.
