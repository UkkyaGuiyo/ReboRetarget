# Research-first engineering

Accepted user directive: 2026-09-05. Standing reinforcement of autonomous authority, Legal/Provenance, Scope Guard and Safety Gates; not a new permission for Live, output, UI, application operations or architecture changes.

**Think first. Search early. Verify locally.** Ability to invent a solution is not a reason to ignore existing work.

## Before a substantial change

1. State the specific problem and a falsifiable initial hypothesis.
2. Search existing knowledge early: official capabilities, specifications and GitHub implementations.
3. Read relevant source, examples and tests, not only repository names or README claims.
4. Search issues, pull requests and discussions, including closed reports. Distinguish fixed, by-design, rejected workaround and unresolved limitation; an issue report alone is not confirmed causality.
5. Compare the evidence with the hypothesis and revise or reject it when contradicted.
6. Choose the smallest safe local experiment. Preserve existing acceptance conditions and measure the actual requested result.

For a new major implementation, record an **External Research Gate**: official sources checked; prior implementation searched; issues/PRs searched; freshness checked; license checked. Do not begin a major feature with all five unchecked. A blocked search or missing evidence is UNVERIFIED, not an invented PASS; use an accessible primary source or record why the unknown blocks adoption.

This is not a mandatory research ceremony for typos or already-evidenced small edits. Reuse relevant evidence, refreshing drift-prone facts when needed. Usually 3–10 strong sources and sufficient independent agreement are enough; do not spend time collecting hundreds of repositories.

## Evidence priority and quality

- Tier 1: ReboCap, VRChat, Valve/OpenVR, OSC, Microsoft, Python and Unity official documentation/repositories.
- Tier 2: relevant maintained OSS implementations, including SlimeVR, ReboSlime, Virtual Motion Tracker and community OSC/retargeting projects.
- Tier 3: issues/PRs/discussions, particularly real failures, compatibility constraints and abandoned approaches. An upstream project's own implementation/fix is primary evidence for that project.
- Tier 4: blogs, forums and Reddit as supplementary operational leads, never the sole authority for a wire specification.

Search by symptom and exact symbols/addresses as well as project name: callback drops, 60Hz consumer jitter, `/tracking/trackers/`, `TrackedDeviceClass_GenericTracker`, `TrackerRole_`, `perf_counter`, capacity-one/latest-frame handoff. Use GitHub code search when available; an inaccessible authenticated search is not permission to bypass access controls. Read public repository files/tree or upstream sources instead.

Check target software/interpreter/platform, last relevant commit, release, issue date/status, PR merge date and documentation update. Pin important source observations to a revision or release. Label old material **historical reference** rather than applying it directly to today's system.

Evaluate maintenance, issue responsiveness, tests, releases, license, dependencies, complexity and feature fit; stars are not an acceptance criterion. A license on one repository does not grant rights to bundled third-party SDKs. Absence of a date/license is an explicit uncertainty.

## Problem-specific comparison candidates

| Problem | Search candidates and focus |
|---|---|
| Tracking loop / pose freshness | SlimeVR Server update loop, skeleton cadence, smoothing and latency; relevant issues/PRs |
| ReboCap input | ReboSlime callback, joint selection, quaternion handling, lifecycle/error handling; verify against official SDK semantics |
| VRChat output | Official docs, vrchat-community and active OSC implementations; numbered slots, cadence, FBT calibration, head alignment, duplicate sources |
| SteamVR virtual tracker / role | Official OpenVR examples/API, VMT, SlimeVR OpenVR bridge before any custom driver design |
| Windows Python scheduling | Python/Microsoft docs and upstream bugs; realtime camera, robotics, mocap, game input and audio patterns where constraints match |
| Retargeting / contact / smoothing | Existing skeleton/FK/coordinate/OSC/retarget implementations before inventing a new layer; no authority to implement currently deferred features |

These are search candidates, not preapproved dependencies or automatically correct designs. Do not transplant SlimeVR's server/solver architecture into the project merely because it exists.

## Adoption and provenance

Compare external design versus ReboRetarget on latency evidence, complexity, dependencies, safety, maintainability and feature fit. Classify findings as relevant, irrelevant, outdated/historical or promising. Return only findings affecting the current decision, not a search-results dump.

Learn algorithms, failure patterns, API usage and timing/coordinate conventions. Do not copy code without a verified compatible license and attribution obligations; understanding and reimplementing an idea is not permission to translate protected source. No proprietary/leaked/decompiled source, pirated SDK, unclear-license code, authentication/DRM/payment/license/security bypass or unauthorized access.

Use independent subagents for distinct research questions when parallelization is useful; the main agent integrates conflicting evidence and retains safety responsibility. Do not duplicate identical searches for agent count alone.

Important decisions get a compact evidence table in `RESEARCH_LOG.md`: question, exact source URL/revision/release or issue/PR, access date, finding, confidence and applicability. Distinguish observations from inference, proposed experiments from executed changes, and synthetic results from Live results.

## Current application

The initial comparison is research-only. The existing 216-test three-version checkpoint, pure p99 1.4271ms and synthetic consumer 58.88Hz remain historical measured evidence, not new benchmark results. A rewrite needs concrete benefit and evidence. Phase 2F-A remains WAITING_FOR_USER for renewed readiness and a fresh Safe Point; this directive does not start another cue or authorize OSC/VR operations.
