# Research Log

Use this file for durable evidence that affects implementation: confirmed facts, failed experiments, rejected approaches, uncertainty, and items worth rechecking. Do not use it as a session diary.

## Entry format

For each material investigation record:

- Date and question.
- Environment/version.
- Source or exact evidence location.
- Observation, clearly separated from inference.
- Result: confirmed, rejected, failed, inconclusive, or needs recheck.
- Consequence for a decision or next task.
- Any user-visible side effect or confirmation still required.

Do not paste secrets, personal data, device identifiers, proprietary binaries/code, or unredacted raw logs into the repository.

## 2026-09-04 — Repository foundation inventory

- Question: Is there an existing ReboRetarget foundation to preserve or merge?
- Evidence: top-level and recursive local file inventory; Git status/config/remote inspection.
- Observation: The repository contained only `.git`; branch `master` had no commits; no remote, project files, foundation archive, or LICENSE existed.
- Result: confirmed for the time of inspection.
- Consequence: All foundation documents in this task are new; there was no project-file conflict or merge. GitHub publication and license selection remain open.

## 2026-09-04 — Global Codex configuration safety check

- Question: Does a global Codex instruction file exist, and must this project modify it?
- Evidence: read-only inventory of the user's global Codex configuration directory; inspection of the existing global `AGENTS.md` and relevant configuration.
- Observation: A substantial global `AGENTS.md` already requires original-request fidelity, minimal action, evidence-based verification, and scoped state updates. The repository is already trusted in `config.toml`.
- Result: confirmed; no global addition is needed.
- Consequence: Global files were left unchanged. ReboRetarget-specific instructions live only in this repository.

## Known rejected or deferred directions

- Uniform tracker-coordinate scaling: rejected as the core solution because segment ratios differ independently.
- Dropping knee trackers: rejected because it loses captured knee intent.
- Dropping shoulder information because VRChat lacks a shoulder slot: rejected; use it inside the upper-body solver.
- Quest IOBT as the normal full-body source: rejected; ReboCap remains primary.
- Automatic avatar skeleton analysis and virtual controllers: deferred beyond the initial version.
- Mesh-surface collision/penetration correction: outside the initial scope.
- Starting with an internal hook or ReboCap binary modification: rejected as the default; use the least-invasive interface order.
- A custom SteamVR driver and speculative infrastructure: not justified by current requirements.

## Open research queue

1. Installed ReboCap version and authoritative SDK/API/license sources.
2. Skeleton joint schema, coordinates, units, handedness, timestamps, and update cadence.
3. Safe read/query/toggle surface for native SteamVR body-tracker output.
4. Current VRChat OSC tracker schema, coordinate system, activation, calibration, and update behavior.
5. Feasible supported mechanisms for auto-start and attached/adjacent UI.
6. Crash-detectable state restoration that never fabricates a prior setting.
7. Measurable latency/jitter budget and where smoothing already occurs.
8. Quest IOBT chest-yaw accessibility and signal quality, as an independent research track only.
