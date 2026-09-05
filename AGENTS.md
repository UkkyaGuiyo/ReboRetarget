# ReboRetarget: Codex entrypoint

## Purpose

ReboRetarget aims to reconstruct motion captured by ReboCap on a VRChat avatar whose bone proportions differ from the user's body. The long-term goal is natural real-time full-body tracking in a Meta Quest 3, Virtual Desktop, SteamVR, VRChat, and ReboCap environment.

This file is only the entrypoint. Do not turn it into the full specification.

## Canonical documentation

Treat these files as the repository's durable project memory:

1. `docs/PROJECT_CHARTER.md` — stable purpose, scope, and long-term goal.
2. `docs/DECISIONS.md` — accepted decisions and their reasons.
3. `docs/CURRENT_STATE.md` — current implementation state and the single recommended next task.
4. `docs/ROADMAP.md` — staged development order and MVP boundary.
5. `docs/RESEARCH_LOG.md` — evidence, failures, rejected ideas, and open research.
6. `docs/INTERFACE_CONTRACT.md` — confirmed external boundaries and the next PoC acceptance gate.
7. `docs/QUEST_CHEST_YAW_ANCHOR.md` — optional future research, separate from the core MVP.
8. `docs/AUTONOMOUS_ENGINEERING_AUTHORITY.md` — accepted autonomous-work levels and bounded Phase 2E recovery permission; read before any new live investigation.
9. `docs/RESEARCH_FIRST_ENGINEERING.md` — standing external-research gate; read before new substantial design, implementation, performance or compatibility work.

If these documents disagree, prefer the user's latest explicit instruction, then the original request, then accepted decisions, then verified real-environment evidence, then `CURRENT_STATE`, and finally older plans or notes. Do not silently delete a conflict; resolve it from evidence or record it as unresolved.

## Start-of-session rule

Before changing anything:

1. Read this file and `PROJECT_CHARTER`, `DECISIONS`, `CURRENT_STATE`, and `ROADMAP`.
2. Read `INTERFACE_CONTRACT`, `RESEARCH_LOG`, or the Quest document when relevant to the current task.
3. Check the current working folder, applicable instructions, `git status`, and relevant diffs.
4. Restate the requested end state, observable acceptance condition, constraints, non-goals, and the minimum action.
5. Verify uncertain behavior from the installed environment, official documentation, source, examples, tests, issues, or release notes before inventing a solution.

Plans and historical notes do not prove that a feature exists. `CURRENT_STATE` is the status index, but confirm drift-prone facts cheaply when possible.

## Non-negotiable principles

- Reconstruct joint motion on a target skeleton; do not reduce the problem to multiplying tracker coordinates by one scale.
- Preserve ReboCap knee and shoulder information as solver inputs as documented in `DECISIONS.md`.
- Preserve the normal Quest controller hand route for the initial version.
- On Retarget ON/OFF, change only what is necessary for ReboCap's SteamVR body-tracker output and restore the exact prior state. Never assume the previous state was ON.
- Treat sensor assignments, shoulder tracker assignments, AI Engine, 6-axis/magnetic choices, Ground IK, skeleton settings, native calibration, and other user-tuned ReboCap settings as protected unless a later explicit, evidence-backed decision says otherwise.
- During a live Quest/Virtual Desktop/SteamVR/VRChat/ReboCap session, prefer read-only logs, files, APIs, and process inspection. Do not foreground, restart, stop, reset, or change a connected component without explaining the exact impact and obtaining explicit authorization.
- Prefer the official SDK/API, then configuration, local IPC/API, Windows UI Automation, and only lastly internal analysis or hooking. Reverse engineering is limited to interoperability; do not bypass authentication, payment, or licensing.
- Do not commit proprietary third-party binaries/code, personal data, device identifiers, secrets, or raw user logs.
- Favor low latency, low jitter, latest-pose processing, and avoidance of duplicated smoothing.

## Scope discipline

Think first. Search early. Verify locally. Before a substantial implementation, check official specifications, GitHub source/examples/tests, relevant issues/PRs (including closed outcomes), freshness and licenses. Use the bounded research gate in `docs/RESEARCH_FIRST_ENGINEERING.md`; external examples neither authorize live operations nor justify wholesale architecture replacement.

Implement only the smallest change that advances the current accepted goal. Do not prebuild a plugin system, DI container, event bus, database, repository framework, custom SteamVR driver, or extra communication layer. Keep responsibilities separable only to the degree justified by current work.

The user's hypotheses are valuable inputs, not immutable facts. If verified evidence contradicts one, explain the evidence and correct the documentation rather than preserving a known error.

Do not claim completion from a setting, test, or upstream signal when the acceptance condition names an actual VRChat/SteamVR/ReboCap output surface.

## End-of-session rule

Before declaring work complete:

1. Verify the requested observable result at the required surface.
2. Update only the canonical files whose facts or decisions actually changed:
   - `CURRENT_STATE` for progress, evidence, blockers, and the next task;
   - `DECISIONS` only for an accepted decision or a superseded decision;
   - `RESEARCH_LOG` only for material evidence, failure, rejection, or an unresolved question;
   - `ROADMAP` only if sequencing or scope genuinely changed.
3. Record what was implemented, what was only tested or documented, what remains unverified, whether anything was deployed or published, and the final `git status`.
4. Avoid diary-like updates and duplicate facts.
