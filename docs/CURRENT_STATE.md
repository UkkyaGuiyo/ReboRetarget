# Current State

Last updated: 2026-09-04

## Current checkpoint

The durable project-memory foundation has been created. The repository now describes the intended product, accepted decisions, staged roadmap, research record, optional Quest chest-yaw research, and Codex start/end rules.

## Actual implementation state

**No ReboRetarget application implementation exists.** Before this foundation task, the repository contained only `.git`. This task adds documentation only.

Not implemented:

- ReboCap SDK/API connection or skeleton ingestion.
- Retargeting mathematics or solver.
- VRChat OSC tracker output.
- GUI, ReboCap-attached window, profiles, or persistence code.
- ReboCap watcher, automatic startup/shutdown, crash recovery, or setting restoration.
- SteamVR output control or UI automation.
- Quest chest-yaw monitoring or correction.
- Tests, builds, packages, releases, deployment, or publication.

## Foundation completed in this task

- Repository entrypoint: `AGENTS.md`.
- Public status summary: `README.md`.
- Canonical documents: `PROJECT_CHARTER`, `DECISIONS`, `CURRENT_STATE`, `ROADMAP`, and `RESEARCH_LOG`.
- Independent future-research document: `QUEST_CHEST_YAW_ANCHOR.md`.
- Memory-build and self-verification report: `CODEX_MEMORY_BUILD_REPORT.md`.

## Verified repository facts

- Git repository exists on branch `master` with no commits.
- No Git remote is configured.
- No prior project/foundation files or archive were present outside `.git`.
- No LICENSE exists; license selection and dependency/SDK compatibility review remain open.
- The user's global Codex instruction and configuration files existed and were inspected read-only. Neither was changed by this task.

## Single recommended next task

Perform a **read-only ReboCap integration discovery** before choosing a technology stack or writing application code:

1. Record the installed ReboCap client/version and locate official SDK/API documentation and license terms.
2. Determine how skeleton pose data can be read, including joint names, coordinate system, units, timestamps, and expected update behavior.
3. Determine whether the SteamVR body-tracker output can be queried and toggled through the official SDK/API, configuration, or local IPC without touching protected settings.
4. Produce evidence, unresolved questions, and a proposed minimal interface contract in `RESEARCH_LOG`; do not implement the app during that task unless the user separately authorizes implementation.

Use the priority order in D-011. If a live VR session is active, use quiet/read-only inspection and do not foreground, restart, stop, reset, or change ReboCap/SteamVR/VRChat/Virtual Desktop/Quest state without explicit authorization.

## Blockers and unverified items

- ReboCap SDK availability, current version, license, skeleton schema, and supported connection model are unverified.
- The actual control surface for ReboCap's SteamVR body output is unknown.
- VRChat OSC tracker protocol details and acceptance workflow have not been verified against current official documentation or the live environment.
- Technology stack and MVP/v1 boundary are not selected.
- Crash-safe restoration behavior has not been designed or tested.
- The Quest chest-yaw signal source, quality, drift model, and usefulness are unverified.

## Repository state at handoff

- Branch: `master`.
- Commit: none.
- Remote/GitHub publication: none.
- Expected dirty files: new documentation files listed above, all uncommitted.
- Deployment: none.
