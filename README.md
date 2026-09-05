# ReboRetarget

ReboRetarget is a planned real-time morphology-retargeting tool for adapting ReboCap body motion to VRChat avatars with different skeletal proportions.

## Status

Research-core stage. Phase 2A–2D provide a pure standard-library FK core, ReboCap T-pose-delta adapter, eight semantic anchors and network-free VRChat OSC representation/codec. Phase 2E passed one supervised Live recovery run with 1200 valid callbacks and 429 memory-only snapshots. Phase 2F-A remains PARTIAL after two incomplete controlled-motion attempts. The subsequent offline recovery adds a local countdown wrapper, reviewed mathematical/cadence optimizations and synthetic performance evidence; see [the performance report](docs/PERFORMANCE_INVESTIGATION_REPORT.md) for full-suite results, measured boundaries and unresolved historical Live causality. Further body cues require renewed explicit user readiness and a fresh Safe Point. No product SDK client, OSC sender, IK, GUI, watcher, native-output switch or VR application has been implemented or deployed.

The intended primary environment is Meta Quest 3 + Virtual Desktop + SteamVR + VRChat + ReboCap. The initial direction preserves Quest controller hand tracking while generating eight planned VRChat OSC tracker outputs from the ReboCap skeleton and manually tuned avatar profiles.

Start with [AGENTS.md](AGENTS.md), then read the canonical documents under [`docs/`](docs/). The implementation boundary is summarized in [`docs/INTERFACE_CONTRACT.md`](docs/INTERFACE_CONTRACT.md).

## Why morphology retargeting?

A single tracker scale cannot correct different thigh/calf, upper-arm/forearm, hip, and shoulder proportions. ReboRetarget is intended to reconstruct captured joint motion on the target avatar skeleton so that straight legs, crossed legs, kicks, crouches, weight shifts, folded arms, and other poses retain their intent.

## Publication and license status

This repository is public at <https://github.com/UkkyaGuiyo/ReboRetarget>. It contains research documentation, the isolated Phase 1.5 aggregate Inspector, the supervised Phase 2E research probe, and pure/offline retarget, sequence, ReboCap-delta-adapter, tracker-anchor, latest-pose state, VRChat representation, and OSC memory-codec code with synthetic tests. It does not contain ReboCap SDK files, proprietary binaries, raw logs, personal motion data, or device identifiers.

No project license has been selected. The downloadable ReboCap SDK archives inspected during Phase 1 did not contain an SDK-level license or redistribution grant. Project licensing therefore remains provisional until the vendor terms and all future dependencies are confirmed. No third-party code is licensed merely by being described or linked here.

Publication constraints and source origins are documented in [`docs/LEGAL_BOUNDARIES.md`](docs/LEGAL_BOUNDARIES.md) and [`docs/PROVENANCE.md`](docs/PROVENANCE.md).
