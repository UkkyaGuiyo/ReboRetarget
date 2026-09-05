# Playtime sampling assessment

Date: 2026-09-05. Status: **RESEARCH ONLY; NO CAPTURE STARTED**.

## Accepted boundary

The user prioritizes normal VRC play and asks us to advance useful work without disturbing it. No additional SDK client, recording, ReboCap/SteamVR/Virtual Desktop/Quest operation, configuration change or heavy benchmark during play. Permission to investigate sampling is not permission to start it. Existing code/tests and public documentation can be examined offline. No computer-use, packet interception, undocumented IPC or proprietary-format reverse engineering is an alternative route.

## Feasibility

| Route | Evidence | Current disposition |
|---|---|---|
| ReboCap standard recording/export | Official documentation describes recording under the PC panel and FBX/BVH/DAE export. | Promising, but simultaneous recording in the current VR mode with unchanged tracking is UNVERIFIED. No recorder/importer implementation yet. |
| PC-mode VR Output | Official documentation describes virtual-skeleton points unaffected by the HMD. | Not equivalent to preserving the current VR-mode route. Do not switch modes or outputs to obtain a recording. |
| Vendor diagnostic recording | Official configuration documentation describes encrypted developer-diagnostic data. | Not an established accessible skeleton export; do not save/decrypt it or substitute it for standard recording. |
| Additional official SDK receiver | Existing single-client value-path PASS, earlier concurrent crash with unresolved cause. | Coexistence is not proven. No new client during play under current authority. |
| Existing synthetic poses and aggregate evidence | Already available in this repository. | Use now; no personal motion capture or runtime connection required. |

Primary sources checked on 2026-09-05: [Connection](https://doc.rebocap.com/en_US/ui_help_doc/control/connect.html), [Chinese original](https://doc.rebocap.com/zh_cn/ui_help_doc/control/connect.html), [Configuration](https://doc.rebocap.com/en_US/ui_help_doc/control/config.html), [SteamVR integration](https://doc.rebocap.com/en_US/third_party_software_access/steamvr/), [SDK](https://doc.rebocap.com/en_US/SDK/). Standard recording and SteamVR being separately documented does not establish simultaneous compatibility. No explicit guarantee was found in this bounded review; absence of documentation is not proof that it is impossible.

## What natural motion can establish

If a supported recording route is later approved, short natural-motion samples can reveal motion coverage, numerical discontinuities and adjacent-joint rotation relationships. They can supply private offline regression cases after their skeleton, units, rotations and sampling semantics are verified.

They cannot independently identify physical right/up/forward, true anatomical pose, optional sensor ownership, shoulder-tracker independence or avatar accuracy. Joint correlation is not sensor attribution. Uniform export frame spacing is not measured SDK arrival jitter; exported animation may omit original timestamps or alter root/rest transforms. Do not infer physical latency, live callback cadence or SDK delta semantics from an export without evidence. Known-motion tests remain a separate short post-play task.

## Smallest future capture gate — proposal, not authorization

1. Confirm the installed version officially supports recording while remaining in VR mode, with no change to native output, HMD contribution, calibration or protected settings. Stop this route if it requires changing any of them.
2. Obtain explicit approval for a specific recording route, short duration and raw-data policy. Propose one 30-second clip, not continuous capture or automatic retries. The user starts/stops only the supported recorder; no automation is prepared now.
3. Agree on a private, non-synchronized location outside this repository and a deletion/retention period before saving. This repository is under OneDrive and may synchronize; its current sync status was not inspected. Ignored files here are not necessarily private local-only files. Do not collect audio/video, other players' conversations, identifiers or credentials.
4. If an adverse change occurs, end only the added recording/client using its supported normal stop; leave the VR stack and ReboCap intact. Do not promise zero disturbance or automatic recovery before coexistence is tested. No forced shutdown or reconnect.
5. Analyze after play. Establish the actual file semantics before building an importer; persist only approved aggregates publicly. Raw personal sequences remain private, even if converted to another format. Synthetic replacements must be independently authored, not mislabeled personal data.

### Vendor question draft — not sent

Does the current ReboCap version support standard motion recording/export while remaining in VR mode with SteamVR and VRChat active, without changing tracker output, HMD-based positioning, calibration or sensor settings? If yes, what is the supported start/stop procedure and which formats preserve joint rotations, hierarchy, root translation and original sample timing? Are there known load/coexistence limitations? Separately, is one official external SDK receiver alongside the normal VR route supported?

No inquiry was sent and no installed application was operated for this assessment.

## Prioritized remaining work

| Task | Impact / confidence / risk | Dependency / user required | Decision |
|---|---|---|---|
| Finalize corrected wrapper evidence and current safety status | High / high / low | Existing tests and reviews / no | Completed offline; see `PHASE_2F_A_REPORT.md`. |
| Confirm standard recording compatibility | High / medium / low for document research | Vendor/version evidence / possibly inquiry approval | Bounded research complete; compatibility still UNVERIFIED. |
| Representative four-stage wrapper timing | High / high / potentially disruptive during play | Quiet measurement period / play finished | Deferred; keep strict pure p99 <10ms and report whole-wrapper timing separately. |
| Short labeled right-motion cue | High / high / live interaction | Timing/readiness/fresh Safe Point / yes | Deferred; no old readiness reuse. |
| Passive SDK collection or raw export | Medium / low until coexistence confirmed / live + privacy | Supported route and explicit collection approval / yes | Not started. |

No sampling framework, recorder, exporter, proprietary parser or extra runtime was built merely to fill this waiting period.
