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

## 2026-09-04 — Public baseline and safety boundary

- Question: Can the documentation baseline be published without exposing private or proprietary material?
- Evidence: staged-file inventory, secret/email/local-path pattern scans, diff checks, Git history, and GitHub repository readback.
- Observation: The Phase 0 commit contains nine Markdown files only. Local user paths found during the pre-publication scan were replaced with generic descriptions. No third-party binary, SDK archive, raw log, motion recording, device identifier, secret, or unnecessary email address was committed.
- Result: confirmed. Commit `bc01e74` is published on public `main` at <https://github.com/UkkyaGuiyo/ReboRetarget>.
- Side effect: repository creation and push only; no VR application/process/setting change.

## 2026-09-04 — Installed ReboCap and local integration surface

- Question: What can ReboRetarget safely read from the installed application without disturbing the live environment?
- Environment: ReboCap uninstall label `Release V02 Beta_02`; executable metadata product version `0.48.0.0`, file version `1.0.0.0`. The differing version surfaces are recorded rather than collapsed into one value.
- Evidence: uninstall registry metadata, file version metadata, read-only install inventory, configuration key inspection, installed OpenVR driver resources, and sanitized historical log classification. No running ReboCap, SteamVR, or VRChat process was found; Virtual Desktop was left untouched.
- Confirmed observations:
  - ReboCap packages a WebSocket SDK DLL and an OpenVR driver named `rebocap`.
  - The driver is installed inside SteamVR's driver directory and declares itself always active.
  - Driver profiles identify devices as `TrackedDeviceClass_GenericTracker` and define waist, chest, knee, ankle, foot, shoulder, elbow, wrist, and unassigned tracker types.
  - Historical local driver logs show ReboCap devices registered as OpenVR class 3. Raw logs and identifiers are not retained here.
  - The main configuration store contains output-node and PC-VR-output field names alongside shoulder/sensor assignment, AI, Ground IK, skeleton, calibration, and six-axis fields.
  - The store is custom/pickle-derived binary data rather than a stable documented configuration API.
  - No dedicated ReboCap registry setting for the output switch was found.
- Result: confirmed for installed artifacts; live poses and output-OFF behavior not tested.
- Consequence: direct configuration rewriting is rejected. A supported stateful switch or narrow, user-authorized UI fallback must be proven before automatic mode switching.

## 2026-09-04 — Official ReboCap SDK and skeleton contract

- Question: Is there a supported low-latency skeleton input, and what exactly does it provide?
- Sources: <https://doc.rebocap.com/en_US/SDK/>, official Python/C#/C++ SDK downloads linked there, and ReboCap UI documentation.
- Confirmed observations:
  - All SDKs/plugins use the ReboCap GUI's WebSocket broadcast. Default port is `7690`; ReboCap increments the port if occupied.
  - The official DLL exposes eight functions covering instance creation/release, open/close, pose callback, abnormal-close callback, last-message read, and foot-vertex calculation.
  - Data starts after user action calibration and is documented at 60 fps.
  - Regular Pose data is pelvis translation in metres, 24 quaternions, foot/contact index, and timestamp. It does not include a world position for every bone.
  - The 24 names are Pelvis; left/right Hip; Spine1; left/right Knee; Spine2; left/right Ankle; Spine3; left/right Foot; Neck; left/right Collar; Head; left/right Shoulder; left/right Elbow; left/right Wrist; left/right Hand.
  - Default output is OpenGL right-handed; Unity, Blender, Maya/Max, and UE variants are available. Local rotations are parent-relative and all rotations are relative to T-pose; global rotations can be requested. Examples label quaternion components `(w,x,y,z)`.
  - The SDK schema always includes shoulder-related joints but no physical-shoulder-tracker presence flag.
- Unverified: timestamp epoch/unit after language-wrapper conversion, normative parent array, multi-client support, live cadence/jitter, and shoulder-present/absent signal differences.
- Result: sufficient static contract for a read-only live Pose PoC.

## 2026-09-04 — ReboCap SDK license and redistribution

- Question: May the SDK be copied into this public repository or redistributed with future builds?
- Evidence: official Python v2, C# v2, and C++ v3 archives downloaded to a temporary directory outside the repository; archive inventories and documentation footer inspected.
- Observation: no SDK-level `LICENSE`, `NOTICE`, or `COPYING` file and no explicit redistribution grant was found. A vendored dependency's license does not license the ReboCap SDK itself. Official documentation carries an all-rights-reserved notice.
- Result: redistribution permission is unconfirmed, not presumed denied or granted.
- Consequence: no SDK code/binary is committed; project license remains provisional. Vendor clarification is required before bundling the SDK.

## 2026-09-04 — Native SteamVR output control

- Question: Can ReboRetarget safely query, disable, and exactly restore only native ReboCap body trackers?
- Sources: installed configuration/driver artifacts and <https://doc.rebocap.com/en_US/ui_help_doc/control/connect.html>.
- Confirmed observations:
  - The public SDK has no SteamVR-output switch function.
  - The official UI documents a PC-side advanced `VR Output` toggle and VR-panel node selection.
  - Local symbols/configuration identify plausible UI/state fields and named-pipe communication, but not a supported external query/set/acknowledgement contract.
  - PC-side `VR Output` is not documented as a universal master for the separate VR motion-capture mode.
- Internal analysis performed: string/export inspection only, limited to interoperability facts. No decompiled source was copied or published.
- Result: inconclusive for safe automatic ON/OFF; direct config edit rejected.
- Next evidence: at an explicit safe point, compare exact setting readback, driver devices, and unrelated-setting hashes for manually toggled states. Do not repeat calibration or change protected controls.

## 2026-09-04 — Current VRChat OSC tracker contract

- Sources: <https://docs.vrchat.com/docs/osc-trackers>, <https://docs.vrchat.com/docs/osc-overview>, and <https://docs.vrchat.com/docs/full-body-tracking>.
- Confirmed observations:
  - Default inbound UDP port is `9000`; it is configurable by VRChat launch option.
  - Eight numbered tracker slots accept separate world-position and Euler-rotation messages, each as three floats.
  - Coordinates use Unity conventions: left-handed, `+Y` up, one unit per metre. Euler values are degrees and applied `Z, X, Y` internally.
  - Maximum roles are hip, chest, two feet, two knees, and two elbows/upper arms. An upper-arm-mounted tracker controls both elbow and shoulder.
  - FBT must be calibrated in VRChat. Optional head position and rotation provide position/yaw alignment with documented single-message versus streaming behavior.
  - VRChat explicitly warns that fewer accurate points may outperform all eight when extra points drift or are inaccurate.
- Inconclusive: duplicate-role precedence when native SteamVR and OSC trackers coexist; no deterministic behavior is promised.
- Consequence: planned eight semantics remain valid but are enabled by observed quality, and native ReboCap body output must not be left ambiguously duplicated in production mode.

## 2026-09-04 — OSS comparison

| Project | Maintenance evidence | License | Relevance and decision |
|---|---|---|---|
| [colasama/ReboSlime](https://github.com/colasama/ReboSlime) | Latest repository commit found: 2024-04-06; README release `v0.4.2` | MIT | Directly proves official ReboCap global quaternions can feed a live tracker pipeline and documents a conventional parent array. Not adopted: it converts rotations into SlimeVR IMUs, adds another server/solver hop, does not provide per-bone positions or morphology retargeting, and targets older ReboCap generations. |
| [SlimeVR/SlimeVR-Server](https://github.com/SlimeVR/SlimeVR-Server) | Active 2026 commits/releases | Dual MIT/Apache-2.0 | Strong reference for real-time pose buffering, tracker semantics, OSC/VMC/OpenVR integration, and operational robustness. Not a base: far larger than the minimum adapter/solver and would add an unnecessary server and solver. |
| [gpsnmeajp/VirtualMotionTracker](https://github.com/gpsnmeajp/VirtualMotionTracker) | Latest repository commit found: 2023-02-02 | MIT | Useful OpenVR/OSC virtual-tracker reference. Not adopted because direct VRChat OSC removes the custom-driver layer and Phase 1 explicitly excludes a new SteamVR driver. |
| [DenTechs Virtual Desktop Body Tracking Configurator](https://github.com/DenTechs/Virtual_Desktop_Body_Tracking_Configurator) | Repository updated 2024; release 1.8 observed in 2026 search | MIT | Useful only for recognizing Virtual Desktop's separate emulated-tracker configuration boundary. It does not control ReboCap and must not be used to alter the user's VD setup for this project. |
| [Valve OpenVR](https://github.com/ValveSoftware/openvr) | Official current SDK/docs | BSD-3-Clause | Authoritative reference for `GenericTracker`, role storage, and device-path semantics. Read-only inspection reference only; no custom driver planned. |
| [VRChat OSC repositories/examples](https://github.com/vrchat-community/osc) | Current community/official documentation mirrors | MIT | Useful packet and calibration examples. Adopt protocol facts, not a full application architecture; the official example itself warns its hard-coded scale is only a starting point. |

## Updated open research queue

1. Live official-SDK callback validation on the currently installed ReboCap build.
2. Timestamp semantics, measured 60 Hz cadence/jitter, axis/quaternion/hierarchy checks, reconnect, and safe multi-client test.
3. Controlled shoulder-trackers-present versus absent comparison without changing the user's calibration/settings unexpectedly.
4. Safe native-output state query/set/restore and manual-toggle A/B evidence; direct config writing remains rejected.
5. Real VRChat test of origin/yaw alignment, point quality, packet rate, reduced versus eight-point configurations, and duplicate-source behavior.
6. Vendor clarification for SDK redistribution/bundling.
7. Quest chest-yaw accessibility remains independent and non-blocking.

## 2026-09-04 — Phase 1.5 live Pose observation

- Question: What does the installed ReboCap build emit during ordinary use through the official SDK, without retaining raw motion or sending output?
- Environment: an already-running calibrated ReboCap, SteamVR, Virtual Desktop, and VRChat session; official Python SDK loaded from outside the repository; `UnityCoordinate` and global rotations.
- Evidence: aggregate-only output from `research/live_pose_inspector.py`; 29,233 callbacks across 487.658 seconds. The aggregate file and raw application logs are not retained in the repository.
- Confirmed timing observations:
  - Average callback rate was 59.9436 Hz. Receive interval median was 16.5 ms (60.6061 Hz), p95 17.8 ms, p99 18.3 ms, and maximum 130.4663 ms.
  - There were 15 receive gaps at least 50 ms, 7 at least 100 ms, none at least 250 ms, 64 intervals below 4 ms, and 6 gap-followed burst candidates.
  - Source timestamps were Unix seconds after wrapper conversion. All 29,232 deltas were monotonic; median source interval was 16.9 ms, p95/p99 18.0 ms, and maximum 51.0001 ms. No source jump of at least 250 ms occurred.
  - Receive-minus-source difference was median 0.3 ms, p95 0.9 ms, p99 1.1 ms, with a 173.8474 ms connection-start maximum consistent with initial catch-up.
- Confirmed Pose observations:
  - Every callback contained 24 joints and every Quaternion sample was finite and normalized within `1e-7`; invalid frames were zero. The SDK wrapper/example order `(w,x,y,z)` was used.
  - Pelvis translation remained finite. Its observed XYZ range was `(0.798379, 0.743274, 0.816602)` metres and maximum single-frame displacement was 0.019721 metres.
  - Collar, Shoulder, Elbow, Wrist, Hip, Knee, Ankle, and Foot streams all changed continuously. Shoulder and Elbow activity exceeded Spine activity in this session.
  - R_Shoulder/R_Elbow, each Wrist/Hand pair, and each Ankle/Foot pair produced identical aggregate motion statistics. These pairs are not treated as proven independent degrees of freedom.
  - `static_index` was `-1` for every callback, so contact/static behavior was not demonstrated.
- Inference: the input quality is sufficient to begin a pure Target Skeleton FK transform PoC. The gap/burst pattern supports latest-Pose consumption rather than replaying an accumulated FIFO.
- Unverified: known-action axis signs, local hierarchy, independent Foot and Hand information, shoulder-tracker-present versus absent effect, chest Yaw drift separated from voluntary turning, and external disconnect/reconnect behavior.
- Privacy/result: no raw Pose frames, identifiers, absolute local paths, account data, or unredacted logs are committed. The Inspector is research-only and does not bundle the official SDK.

## 2026-09-04 — VRChat incident during Phase 1.5 observation

- Question: Did the Inspector terminate VRChat, and is live multi-client SDK observation proven safe?
- Evidence: process history, VRChat logs and Windows crash evidence, Inspector command history, and the later restart observation. Raw logs and local paths are not retained here.
- Confirmed observations:
  - The first VRChat instance crashed in `UnityPlayer.dll` with access violation `0xc0000005` while the Inspector was connected.
  - No VRChat stop/kill command was issued by the Inspector or Codex. The Inspector only opened the confirmed ReboCap WebSocket endpoint and recorded aggregates.
  - The Inspector was stopped immediately after the user raised the incident.
  - A later short relaunch failure was a Watcher startup race. After correcting the Watcher, VRChat remained running for more than 120 seconds with the Inspector disconnected.
- Result: the direct crash cause remains inconclusive. Temporal overlap does not prove the Inspector caused it, and absence of a kill command does not prove that an additional SDK client could not contribute indirectly.
- Consequence: do not claim Phase 1.5 was non-disruptive. Do not reconnect an additional live SDK client until a separately authorized, controlled safety check is defined. Continue only with a pure/offline Target Skeleton FK transform PoC; keep OSC, IK, native-output switching, and Watcher integration out of that step.

## 2026-09-04 — Phase 2A pure/offline Target Skeleton FK

- Question: Can a global-rotation source pose be reconstructed on a target skeleton with different segment lengths while preserving joint posture rather than source joint positions?
- Environment: Python 3.10.11 standard-library implementation, additionally exercised on Python 3.11 and 3.13; hand-authored synthetic skeletons and poses only. No ReboCap SDK/process/network, Quest, Virtual Desktop, SteamVR, VRChat, OSC, Tracker, Watcher, or UI access.
- Evidence: `reboretarget/fk.py`, `tests/synthetic_fixtures.py`, and 30 passing `unittest` cases in `tests/test_fk.py`; numeric details in `OFFLINE_FK_POC_REPORT.md`.
- Confirmed observations:
  - The exact confirmed ReboCap 24-name order can be strictly validated and converted from ordered `(w,x,y,z)` global rotations into immutable internal values.
  - With Hamilton active rotations, `inverse(parent_global) * child_global` recovers identity and compound child-local rotations. Tests also cover multiplication order, non-identity source/target rest rotations, and `q/-q` equivalence.
  - Motion delta `inverse(source_rest_local) * source_local`, followed by `target_rest_local * delta`, preserves the same local joint posture on a different target rest skeleton.
  - FK using target rest-local vectors leaves a straight knee straight for both a 1.02 m long target leg and a 0.70 m short target leg. Knee 90 degrees and Hip 30 plus Knee 45 degrees produced their analytic target positions and rotations.
  - Left/right mirrored fixtures produce mirrored positions with equivalent rotations. Parent-world rotation correctly rotates child rest vectors.
  - A per-joint source-local diagnostic preserves exact 0-degree inheritance, a measured 15-degree independent rotation, a small 0.05-degree rotation, and left/right 0/12-degree asymmetry as numbers. It intentionally does not classify them or explain why a live pair is equal.
  - `Leg Length` scales total thigh-plus-calf length; `Thigh / Calf Balance` transfers a share between segments without changing that total.
- Result: confirmed for pure synthetic mathematics. Phase 2A acceptance tests passed on Python 3.10, 3.11, and 3.13 (`Ran 30 tests`, `OK` for each runtime).
- Consequence: proceed only to a short hand-authored or lawfully sanitized ReboCap-shaped offline sequence. Live SDK input, OSC, IK, avatar extraction, and VR application integration remain separate No-Go gates.
