# ReboRetarget

ReboRetarget is a planned real-time morphology-retargeting tool for adapting ReboCap body motion to VRChat avatars with different skeletal proportions.

## Status

Research and project-foundation stage only. No application, SDK connection, OSC sender, retargeting solver, GUI, watcher, or SteamVR control has been implemented yet.

The intended primary environment is Meta Quest 3 + Virtual Desktop + SteamVR + VRChat + ReboCap. The initial direction preserves Quest controller hand tracking while generating eight planned VRChat OSC tracker outputs from the ReboCap skeleton and manually tuned avatar profiles.

Start with [AGENTS.md](AGENTS.md), then read the canonical documents under [`docs/`](docs/).

## Why morphology retargeting?

A single tracker scale cannot correct different thigh/calf, upper-arm/forearm, hip, and shoulder proportions. ReboRetarget is intended to reconstruct captured joint motion on the target avatar skeleton so that straight legs, crossed legs, kicks, crouches, weight shifts, folded arms, and other poses retain their intent.

## Publication and license status

This repository has no remote and has not been published. No license has been selected. Before public release, choose a project license only after checking compatibility with the ReboCap SDK and every included dependency. Do not add proprietary third-party binaries, personal data, device identifiers, secrets, or raw logs.
