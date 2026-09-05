# Research Log

## Phase 2F-A first controlled cue (2026-09-05)

One authorized rightward-motion session acquired a 60-sample neutral baseline, but the acknowledged hold did not reach the child within its 20-second marker limit. Held/returned windows are empty, so axes and joint semantics remain UNVERIFIED. Input continued at 60.180417 Hz with 2699 valid accepted callbacks and 940 memory pipelines; pure-pipeline p99 11.75 ms exceeded the unchanged 10 ms criterion. Normal supervised exit, protected ReboCap preservation, no remaining probe and no VR application/output operation were confirmed. No automatic reconnect or repeat. See `PHASE_2F_A_REPORT.md` for aggregates, the distinction between timing-association and performance failures, offline tests and remaining gates.

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

## 2026-09-04 — Official ReboCap 24-joint parent hierarchy

- Question: Is the Phase 2A synthetic parent array actually the ReboCap hierarchy, rather than an OSS-derived convention?
- Primary evidence:
  - ReboCap official Unity SDK v4, `Assets/RebocapSdk/DemoScenes/SdkManager.cs:39-64` and enum `Assets/RebocapSdk/RebocapWsSdk.cs:74-99`; official archive SHA-256 `E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF`.
  - ReboCap official Unreal Engine plugin source v2, `Source/rebocap_runtime/Private/rebocap_source.cpp:115-152`; official archive SHA-256 `AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53`.
  - ReboCap official SDK documentation, “SDK Interface Description” and “24 Bone Names,” last edited 2025-04-17 and accessed 2026-09-04: <https://doc.rebocap.com/en_US/SDK/>.
- Confirmed observation: the Unity and Unreal parent arrays agree for all 24 ordered joints. The normalized index array is `(-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19,20,21)`. Unity encodes the root as `-1`; Unreal uses Pelvis self index `0`; ReboRetarget normalizes the root parent to `None`.
- Evidence classification: every normalized relation is `CONFIRMED`. No parent relation remains `CORROBORATED`, `INFERRED`, or `UNKNOWN`.
- Separate uncertainty: parent relation does not prove independent rotational degrees of freedom. The earlier identical Shoulder/Elbow, Wrist/Hand, and Ankle/Foot statistics therefore remain an independence question, not a hierarchy question.
- T-pose semantic gate: official documentation says all output rotations are relative to T-pose. Unity `SdkManager.cs:385-389,432-433` composes the message Quaternion with default bind rotation; Unreal `rebocap_pose_node.cpp:282-308` composes it with T-pose global rotation. A live adapter must represent this explicitly; passing SDK globals straight through as already-composed absolute bind rotations is rejected.
- Privacy/license: only source identifiers, public URLs, file/line references, and archive hashes are retained. Official archives/code are not committed.

## 2026-09-04 — Phase 2B synthetic Pose sequence replay

- Question: Does the Phase 2A pure FK core remain deterministic and continuous across short ReboCap-shaped Pose sequences and target proportion changes?
- Evidence: `retarget_sequence`, synthetic fixture tuples, and 44 passing standard-library `unittest` cases. All inputs are hand-authored; no recording, raw user motion, external dependency, interpolation, clock, device, process, network, or output adapter is involved.
- Confirmed observations:
  - A seven-frame sequence advances Hip by 5 degrees and Knee by 10 degrees per frame from straight to 30/60 degrees. Target Knee/Ankle positions match analytic FK to `1e-9` m; maximum long-target Ankle step is 0.175762206 m and no component-space Quaternion comparison is used.
  - The same sequence preserves identical local rotations on 1.02 m long and 0.70 m short targets. `Leg Length = 1.10` yields 0.473+0.473=0.946 m on every frame.
  - `Thigh / Calf Balance = +0.10` yields 0.516+0.344=0.86 m. In the straight frame the Ankle endpoint is unchanged while the Knee moves 0.086 m; in bent frames the endpoint changes analytically with the segment redistribution rather than being position-locked.
  - Four root frames isolate lateral `+0.20` m, vertical `+0.15` m, and forward/back `-0.30` m translation. Every Target joint receives exactly the same delta and rotations remain unchanged.
  - A four-frame `179, -q(179), -q(181), 181` sequence has shortest Knee-rotation steps `0, 2, 0` degrees, so sign flips and the 180-degree boundary do not create false jumps.
  - A five-frame Spine3/Collar/Shoulder/Elbow sequence preserves incremental local rotations and parent propagation. A fixture-only Shoulder Width scale of 1.10 expands the rest shoulder span from 0.40 m to 0.44 m without changing the 0.28 m upper-arm or 0.25 m forearm lengths.
- Result: Phase 2B offline acceptance passes. Product Arm Length, interpolation, IK, contact locking, and tracker/OSC output were not implemented.
- Consequence: the next smallest gate is pure/offline conversion from Target Skeleton world transforms to the planned tracker transforms. Live SDK connection and OSC transmission remain No-Go.

## 2026-09-04 — Phase 2C ReboCap delta adapter and semantic tracker anchors

- Question: Can official ReboCap T-pose-relative Quaternion semantics be adapted before the source-agnostic FK core, then used to place the planned eight semantic trackers on a Target Skeleton without any live or network integration?
- Evidence: official ReboCap SDK documentation; Unity SDK v4 `SdkManager.cs:385-389,432-433`; Unreal Engine plugin v2 `rebocap_pose_node.cpp:282-308`; `reboretarget/rebocap_adapter.py`; `reboretarget/tracker_anchors.py`; and 61 standard-library `unittest` cases summarized in `OFFLINE_TRACKER_ANCHOR_REPORT.md`.
- Confirmed observations:
  - The pure adapter computes each canonical absolute source global as `sdk_rotation_delta * source_bind_global_rotation`. Identity/non-identity bind and delta cases, a noncommuting order check, a parent-bind plus child-motion case, 24-item validation, hierarchy validation, and exact root-translation passthrough pass synthetically.
  - The FK core remains ReboCap-agnostic. The adapter contains no SDK client, process, network, filesystem, or clock access.
  - Exactly eight immutable semantic transforms are produced from `joint + local offsets`. Synthetic tests cover identity, long/short legs, knee bend, root translation, body yaw, Shoulder Width, Hip Width, mirror symmetry, noncommuting rotation offset, definition validation, and full delta-to-Target-to-anchor integration.
  - Fixture-only Shoulder Width `1.00 -> 1.10` increases Upper Arm anchor span from `0.68 m` to `0.72 m`. Fixture Hip Width `0.20 m -> 0.24 m` shifts each side's Knee/Foot anchor outward by `0.02 m` without moving central or Upper Arm anchors.
- Foot-anchor choice: use `L/R_Ankle` as parent and half the Target `Ankle -> Foot` rest vector as the local position offset. This locates the anchor on the target chain without assuming an independently trustworthy Foot rotation, which the earlier duplicate Ankle/Foot live statistics did not prove. It is a replaceable synthetic fixture, not a product default.
- Result: Phase 2C pure/offline acceptance passes. Arm Length and UpperArm/Forearm Balance remain deliberately deferred; no slot mapping, Euler conversion, packet encoder, UDP/OSC sender, live SDK connection, tracker device, IK, lock, GUI, or VR process access was added.
- Consequence: proceed only to the pure/offline VRChat OSC representation gate. Live input and output remain separate No-Go gates.

## 2026-09-05 — Phase 2D current VRChat OSC representation verification

- Question: Can the eight Phase 2C Quaternion tracker transforms be represented exactly as current VRChat OSC tracker values and OSC 1.0 messages without opening a socket or contacting a live system?
- Primary sources checked:
  - VRChat OSC Trackers: <https://docs.vrchat.com/docs/osc-trackers>
  - VRChat Full-Body Tracking: <https://docs.vrchat.com/docs/full-body-tracking>
  - VRChat IK 2.0 Features and Options: <https://docs.vrchat.com/docs/ik-20-features-and-options>
  - VRChat OSC Overview: <https://docs.vrchat.com/docs/osc-overview>
  - VRChat 2026.1.2 release notes: <https://docs.vrchat.com/docs/vrchat-202612>
  - Unity rotation and coordinate documentation: <https://docs.unity3d.com/6000.0/Documentation/Manual/QuaternionAndEulerRotationsInUnity.html> and <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Quaternion.Euler.html>
  - OSC 1.0 specification: <https://opensoundcontrol.stanford.edu/spec-1_0.html>
- Confirmed interface:
  - Body endpoints are `/tracking/trackers/{1..8}/position` and `/tracking/trackers/{1..8}/rotation`, with three floats. The numbers are transport slots; the current official documentation does not assign a fixed semantic role to each number.
  - Position is world-space Unity coordinates, left-handed, `+Y` up, with one unit equal to one metre. The Phase 2C synthetic Target space already uses those axis labels and metres, so Phase 2D performs no scale or axis inversion. This does not prove installed live ReboCap signs or origin.
  - Rotation is Euler degrees and VRChat applies fixed-world-axis rotations in `Z -> X -> Y` order. Under the repository's Hamilton active convention, reconstruction is `qY * qX * qZ`.
  - Head position and rotation use the fixed `/tracking/trackers/head/...` endpoints and are not a ninth body slot. Head position aligns OSC tracking space to the avatar head-bone root; head rotation controls yaw alignment.
  - The rotation stream rule is explicit: one head-rotation message is an immediate alignment; a second within 300 ms enters streamed mode; a ten-second gap leaves that mode. The 2026.1.2 release notes add an immediate single-pulse head-position snap. The main tracker page still describes continuously supplied head position without documenting a position-side 300 ms threshold or ten-second timeout, so rotation timing must not be copied onto position by inference.
  - VRChat consumes OSC trackers through its existing calibrated FBT behavior, similarly to SteamVR trackers. The user still performs `Calibrate FBT`; duplicate native-plus-OSC role precedence remains unspecified.
- Implemented evidence: `reboretarget/vrchat_osc.py` and 22 Phase 2D `unittest` cases. The converter keeps Quaternion until the output boundary, extracts a deterministic finite Euler branch, and validates rotation equivalence by reconstructing `qY * qX * qZ`. Required axis, compound, +/-90-degree, 179/180/181-degree, and `q/-q` cases pass. An additional fixed-seed 100,000-rotation stress check had zero failures and maximum `1-abs(dot)` error `4.441e-16`. The minimal OSC codec handles NUL termination, four-byte padding, exact `,fff`, and big-endian float32, then decodes only in memory.
- Alignment evidence: a separate yaw-plus-translation rigid transform applied to all eight trackers preserves every pairwise distance and relative rotation. Head-alignment values are represented separately and never enter the body role-to-slot map. Recenter is not implemented.
- Result: 61 previous tests plus 22 Phase 2D tests pass on Python 3.10, 3.11, and 3.13, for 83 total. The synthetic Phase 2C-to-2D path yields eight poses, sixteen unique position/rotation messages, and sixteen successful offline decodes.
- Boundaries: no UDP sender, socket import, OSC transmission, timing loop, process detection, live SDK, ReboCap/VRChat/SteamVR/Virtual Desktop/Quest access, tracker device, IK, lock, GUI, or recenter was added or exercised.
- Consequence: Phase 2D's representation gate passes. The next candidate is a separately designed Live ReboCap Adapter Safety Validation with no VRChat OSC transmission; Phase 2D alone does not authorize live connection or UDP output.

## 2026-09-05 — Phase 2E offline latest-pose state preparation

- Question: Can callback and consumer code share exactly one newest validated value with explicit stale/disconnect behavior, without adding a live SDK client, system clock, scheduler, queue, reconnect loop, or network path?
- Evidence: `reboretarget/latest_pose.py` and 20 deterministic `unittest` cases. The complete 103-test offline suite passes on Python 3.10, 3.11, and 3.13.
- Confirmed behavior: both caller-supplied receive and source timestamps must advance strictly; receive-order rejection takes priority and every rejection leaves state unchanged. Each acceptance increments a never-reused sequence and overwrites the sole sample. Stale and disconnected states clear it, disconnected dominates stale, and explicit rearm preserves both timestamp watermarks and the sequence.
- Stale semantics: age greater than the threshold becomes stale; exact threshold remains valid; a caller-sampled `now` earlier than the accepted receive timestamp remains valid. A new source epoch requires a new slot rather than a watermark reset.
- Rate-shape evidence: deterministic logical 60-to-60, 60-to-30, 120-burst-to-30, consumer-pause, weak-reference/garbage-collection, and producer/consumer Barrier cases confirm latest-only storage without relying on sleep or wall-clock timing.
- Threshold status: tests use 0.250 seconds as a provisional Phase 2E candidate. Phase 1.5 observed a maximum receive gap of 130.4663 ms and zero gaps at least 250 ms, but this is not a product default or live safety proof.
- Concurrency boundary: one standard-library `threading.Lock` makes multi-field transitions atomic. The module starts no thread and contains no SDK type, payload validation, clock read, timer, scheduler, queue/deque, reconnect, metrics subsystem, process/filesystem access, persistence, or logging.
- Ad-hoc benchmark: after 10,000 warm-up pairs on Python 3.13.9, 100,000 samples each measured publish p50/p95/p99 of 6.2/10.7/15.1 microseconds (0.858412 s run), snapshot 3.5/6.2/7.8 microseconds (0.499537 s), and publish-plus-snapshot 8.2/11.0/15.2 microseconds (0.951468 s). This uncommitted local measurement has no pass threshold and is not evidence of live end-to-end performance.
- Result: the offline state prerequisite passes. Phase 2E live adapter execution remains `NOT AUTHORIZED TO EXECUTE / WAITING_FOR_USER` under `LIVE_REBOCAP_ADAPTER_SAFETY_PROTOCOL.md`.

## 2026-09-05 — Phase 2E authorized live adapter attempt

- Question: At a user-confirmed natural Safe Point, can one official SDK receive-only client continuously pass Live ReboCap values through delta validation, the canonical adapter, the capacity-one handoff, Target FK, eight anchors, and memory-only OSC representation/codec within the declared latency budget?
- Safety boundary: ReboCap was already running; read-only preflight found one main process, its expected child, the confirmed listener, no VRChat/SteamVR/Meta/Oculus/headset process, and two unchanged Virtual Desktop background processes. One 20-second client was authorized. There was no reconnect, second client, forced disconnect, application/UI/setting/calibration/native-output operation, OSC/UDP/direct sender, or Raw Pose persistence.
- Implemented evidence: `research/live_retarget_safety_probe.py` plus 15 fake-SDK tests validate exact-once constructor/open/close, retry zero, raw 3-value root and 24 unit-tolerance Quaternion input, timestamp order, delta/canonical construction, 30 Hz latest-only consumption, eight anchors, sixteen in-memory OSC round trips, controlled invalidation, aggregate privacy, and forbidden file/direct-transport APIs. The combined 118-test suite passes on Python 3.10, 3.11, and 3.13.
- Live result: the official local WebSocket connection opened successfully and closed successfully after 20.015 seconds, while the same ReboCap process remained alive. Zero Pose callbacks arrived. Therefore callback cadence, validity, timestamps, adapter success, live overwrite/drop behavior, Target/anchor/message counts, and processing latency have no sample and remain `UNVERIFIED`.
- State evidence: publish count 0, EMPTY snapshots 429, slot replacements 0, sequence-gap drops 0. Controlled final STALE and DISCONNECTED states contained no sample, but because no Live sample ever existed this is not a Live stale-clear proof. Natural disconnect was not triggered; abnormal disconnect remains synthetic-test evidence only.
- Operational finding: the official SDK emitted transient connection diagnostics to the terminal even though the ReboRetarget aggregate object excludes paths, endpoint, identifiers, absolute timestamps, Pose values, and bytes. Nothing from that diagnostic stream or the aggregate JSON was persisted or committed. A future authorized runner should transiently filter vendor stdout and persist only the `RESULT_JSON` aggregate if persistence is needed.
- Interpretation: this is not an invalid-frame or adapter contradiction. The input stream was absent upstream of the callback boundary despite successful transport open, and the allowed one connection does not establish why. Do not retry, inspect UI, change settings, recalibrate, or expand reverse engineering under this authorization.
- Result: **Phase 2E UNVERIFIED**. A future retry requires the user to first confirm that the action-calibrated live skeleton/Pose is visibly updating, then grant a new one-run authorization at a newly confirmed Safe Point. Phase 2F-A remains blocked and separately unauthorized.

## 2026-09-05 — Retry with Virtual Desktop background explicitly allowed

- The user superseded the previous Safe Point blocker: existing Virtual Desktop Service/Streamer and established TCP connections were permitted, with no more termination or configuration operations. Read-only preflight confirmed the same ReboCap process/listener and zero VRChat/SteamVR processes.
- One 20-second probe was launched. It was still alive at 43.1 seconds without an aggregate; the parent then terminated only that verified probe. Exact termination elapsed time was not recorded. SDK open/close status, callback count and pipeline metrics are unavailable, so this is ABORTED / UNVERIFIED rather than confirmed callback zero. ReboCap and the permitted Virtual Desktop background processes survived unchanged.
- Offline comparison found a concrete clock difference: Inspector receives on `perf_counter` (QueryPerformanceCounter, 0.0000001 s resolution) while Python 3.10 probe defaults use `monotonic` (GetTickCount64, 0.015625 s). A concurrent synthetic burst reproduced false equal-receive-timestamp rejection with the latter; high-resolution clock injection accepted all 120 samples. This does not reproduce the native hang.
- Public-wrapper review also confirmed synchronous native open/close/release without Python timeouts. The probe checks its deadline after open and prints after cleanup, leaving the stalled stage unobservable. No Python lock cycle was demonstrated; native GIL/join explanations remain hypotheses.
- See `PHASE_2E_RETRY_REPORT.md` for evidence and limits. Fix/test the clock and improve bounded lifecycle diagnostics offline before another user-authorized connection. No third connection or Phase 2F-A was run.

## 2026-09-05 — Supervised Phase 2E recovery PASS

- Under the new bounded autonomous authority, high-resolution receive timing and aggregate-only lifecycle checkpoints were added to the probe. A separate parent deadline isolates SDK lifecycle calls and retains partial evidence; only its owned child is eligible for termination. The combined 140-test synthetic suite passed on Python 3.10, 3.11 and 3.13 before Live validation.
- Recovery attempt 1 accepted all 1200 callbacks through Delta, Canonical and latest-pose publication. It consumed 429 newest samples and skipped 771 superseded sequences, producing 429 eight-anchor/sixteen-message sets and 6864 memory-only decodes. Input/timestamp rejection was zero. SDK open/close succeeded once each; child exit was normal, with total supervised elapsed 20.249216 seconds against a 45-second deadline.
- First callback delay was 0.205819 seconds; pure consumer pipeline p99 was approximately 3.25 ms and callback-receipt-to-decode p99 18.5 ms. These are research value-path measurements, not physical tracking latency or a product scheduling guarantee. Full sample counts, approximate histogram metrics and limitations are in `PHASE_2E_RECOVERY_REPORT.md`.
- The same ReboCap process/listener and Virtual Desktop processes were preserved; VRChat/SteamVR stayed absent. Application/settings/calibration operations, reconnect, OSC/UDP/direct output sends and Raw Pose persistence were zero. Virtual Desktop remained running intentionally under user permission.
- Result: **Phase 2E PASS**, cycle complete after **1 / 3** allowed attempts. Prior no-callback and missing-aggregate causes remain unresolved; successful recovery does not retroactively establish them. Phase 2F-A now has its Phase 2E prerequisite satisfied but remains separately unauthorized and waiting for user-controlled motion.

## 2026-09-05 — Phase 2F offline recovery and performance investigation

- The later authorized rightward trials remained incomplete (60/0/0, then 60/20/0). Chat/tool-paced cues caused missing windows; their pure p99 11.75/20.05ms are separate performance failures, not evidence that full cue analysis ran. See `PHASE_2F_A_REPORT.md`.
- The fast Phase 2E and Phase 2F starting core were identical. Fixed-fixture A–F tests did not reproduce sustained 20ms performance. cProfile instead measured repeated Quaternion allocation and static bind FK; exact-unit immutable reuse and prepared bind preserve dynamic validation while removing proven work.
- Same fixture, Python 3.10, 3×500, warmup 50: research A pure p99 3.5055→1.4271ms, full p99 5.5122→1.9146ms. All final A–F p99 pass strict <10ms; E has a single 10.6513ms maximum. Deferred F completion analysis remains 100ms-class and is reported separately.
- Synthetic supervisor tests reproduced old 21.6Hz consumption at 30Hz configuration because 33.3ms waits averaged 44ms. Initial wake/reset-at-current-time scheduling did not help; phase-preserving deadlines with latest-only skipped ticks achieved 30.14/58.88Hz for 30/60 targets. No OS timer setting or priority was changed.
- Artificial Python thread contention inflated pure p99 to approximately 17.8–17.9ms with GC either ON or OFF; sampled GC pauses were at most 1.18ms. This provides a plausible mechanism, not retrospective proof of the historic Live cause. No runtime GC or GIL policy change was adopted.
- The exact local countdown/supervisor path completed 60/20/20 in three final silent synthetic runs of 12.06–12.19 seconds, including cleanup. Scheduled markers, human confirmation and audibility remain distinct. Open/close/speech hangs and malformed/no-input outcomes are exercised by bounded owned-child tests.
- All 216 tests passed on each of Python 3.10, 3.11 and 3.13. Per-run evidence, allocation diagnostics, review, publication and remaining limitations are maintained in `PERFORMANCE_INVESTIGATION_REPORT.md` and `PERFORMANCE_RESULTS.json`. This investigation made no Live SDK connection, body cue, actual speech, VR application/settings operation or OSC/UDP send.

## 2026-09-05 — Research-first gate and bounded external comparison

Accessed: 2026-09-05. Starting checkout: `7a3e0051ad4d2373dd88228b5dd57aa80f835259`, clean. Three independent agents researched SlimeVR/ReboSlime, VRChat/OpenVR/VMT and Python scheduling; the coordinator checked canonical boundaries and key upstream claims. Research only: no runtime/source/test change, new dependency, vendor material import, benchmark rerun, Live SDK, speech, body cue, application operation or OSC/UDP output. Previous 216-test/1.4271ms/58.88Hz results are reused evidence, not new measurements.

### Source evidence and applicability

| Question | Source / revision / date | Finding | Confidence / decision |
|---|---|---|---|
| Does SlimeVR prove a different loop is needed? | [VRServer.kt](https://github.com/SlimeVR/SlimeVR-Server/blob/554976390b7ce27e789038fc8cc1ed04df7ae6de/server/core/src/main/java/dev/slimevr/VRServer.kt#L245), main commit 2026-08-20 | The loop reads bridges, ticks trackers, updates the skeleton, writes outputs, then sleeps 1ms. A 1000Hz comment is not measured cadence or a scheduling guarantee. | CONFIRMED source observation. Preserve input/processing separation; do not replace our measured fresh-pose loop with repeated 1000Hz FK or add a server/solver. SlimeVR is not proven equivalent to one atomic capacity-one whole-body Pose. |
| Should smoothing/prediction be imported? | [QuaternionMovingAverage.kt](https://github.com/SlimeVR/SlimeVR-Server/blob/554976390b7ce27e789038fc8cc1ed04df7ae6de/server/core/src/main/java/dev/slimevr/filtering/QuaternionMovingAverage.kt#L57); [issue #1341](https://github.com/SlimeVR/SlimeVR-Server/issues/1341), opened 2025-03-10, closed 2025-07-29 | NONE updates directly; smoothing interpolates over time; prediction retains delta rotations. The issue records asynchronous input/processing and inversion problems, with maintainer references to fixes #1351/#1405. | Relevant historical failure, not a current unfixed bug. DEFER filters; preserve q/-q invariants and first measure actual jitter/latency. No proven benefit for this pipeline. |
| Is a major SlimeVR redesign production evidence? | [PR #1798](https://github.com/SlimeVR/SlimeVR-Server/pull/1798), opened 2026-03-27, OPEN at access; head `f0aae5a2f149e21ce893a0597bcfd701b7eda73a` | Kotlin multiplatform/coroutine rewrite is not merged into inspected main. | PROMISING / DEFER. Do not attribute PR plans or checks to released/current implementation or rewrite our architecture to match. |
| Does ReboSlime replace our SDK handoff/adapter? | [reboslime.py](https://github.com/colasama/ReboSlime/blob/0cdb78b9f1222a7d934efeb55dc16d8d8cda5347/reboslime.py#L28), main commit 2024-04-06; [official SDK](https://doc.rebocap.com/en_US/SDK/), footer 2025-04-17 | Unity/global SDK callback iterates 24 joints and sends selected rotations over UDP directly; the path does not use translation/source timestamp and reconnects on abnormal close. Official docs independently specify T-pose-relative rotations, action-calibration-dependent 60Hz output, callback and get-last-message surfaces. | HISTORICAL implementation reference, not local compatibility or morphology validation. Do not import SlimeVR-specific component/sign changes, callback sending, reconnect, or bundled SDK. Existing receive-only validation/capacity-one/Target FK remain necessary. |
| Do OSC representation/cadence rules change? | [VRChat OSC trackers](https://docs.vrchat.com/docs/osc-trackers), absolute page update date unavailable; [2026.1.2](https://docs.vrchat.com/docs/vrchat-202612), 2026-02-24, build 1800 | Current docs support eight numbered slots, metre Unity positions and degree ZXY rotations. No required send Hz found. Head rotation streaming thresholds are separate from the release's single-pulse head-position snap. Extra inaccurate points may worsen results. | CONFIRMED published boundary; retain representation. Our 60Hz ceiling is not a VRChat mandate. Do not apply rotation timing to position. Page auto-center instructions carry an outdated warning: not a new procedure to automate. |
| Does community calibration experience establish roles? | [OSC issue #151](https://github.com/vrchat-community/osc/issues/151), opened 2022-12-12, OPEN; repo main `db0a0d360a9397f19271dfddf8455ff6d8a95948`, 2022-12-09 | Reports misplaced roles after calibration with SlimeVR/Quest OSC. No verified current reproduction or fix was established in this review. | HISTORICAL report, not wire specification or a demonstrated local bug. Supports retaining actual-avatar calibration acceptance; does not prove deterministic slot-to-body mapping. |
| Is GenericTracker a body-role assignment? | [Valve driver documentation](https://github.com/ValveSoftware/openvr/blob/0924064316de3effbcd1acf1e309182a2deb1c05/docs/Driver_API_Documentation.md#trackers-full-body-tracking) and [header](https://github.com/ValveSoftware/openvr/blob/0924064316de3effbcd1acf1e309182a2deb1c05/headers/openvr.h), commit 2026-03-27 | Device class, controller-role hint/OptOut, tracker-body assignment and OSC slot are different concepts. Body role is normally managed by user tracker settings keyed by device path. Documentation also describes a separate IVRSettings route; class/hint assignment alone is not that route. | CONFIRMED boundary. Do not overstate that roles can never be written by any API; do not interpret documentation as permission to write settings or solve ReboCap native-output switching. |
| Should VMT replace direct VRChat representation? | [VMT source](https://github.com/gpsnmeajp/VirtualMotionTracker/blob/336155b93e2049195b2bc707d959c8207b3da1ef/vmt_driver/TrackedDeviceServerDriver.cpp#L483), main commit 2023-02-02; [PR #10](https://github.com/gpsnmeajp/VirtualMotionTracker/pull/10), opened 2024-07-09, OPEN | VMT registers GenericTracker and can set OptOut separately. A later repository push/dependency PR is not proof the driver main has recent feature maintenance. | HISTORICAL reference only. A driver adds installation, lifecycle, dependencies and safety surface without measured benefit to this memory-only OSC task. REJECT transplantation. |

### Repository quality and provenance

- SlimeVR: non-archived, inspected 2026 main; [README license clarification](https://github.com/SlimeVR/SlimeVR-Server#license-clarification) states MIT/Apache-2.0 dual licensing. Quaternion/skeleton/tracking tests exist; observed upstream [Full Build](https://github.com/SlimeVR/SlimeVR-Server/actions/runs/33394763995) succeeded on 2026-08-31. Upstream CI is not a test on this PC or a latency guarantee. Coroutine rewrite remains unmerged; no migration recommended.
- ReboSlime: non-archived but inspected source is from 2024; MIT [repository license](https://github.com/colasama/ReboSlime/blob/0cdb78b9f1222a7d934efeb55dc16d8d8cda5347/LICENSE). No dedicated test/CI workflow found in the inspected tree. Its third-party SDK binary presence does not establish SDK redistribution rights. Nothing was copied. The earlier log's wording that it "directly proves" a working pipeline should be read as source-level prior implementation evidence, not verified execution here.
- OpenVR: official, non-archived, BSD-3-Clause, inspected 2026 commit. VMT: MIT, non-archived, 2023 main plus open 2024 dependency PR; no current compatibility test was executed. vrchat-community/osc: MIT, inspected 2022 main, not a current specification mirror by itself. This qualifies the older comparison table; current official docs take precedence.
- SDK documentation gives a Python 3.6–3.12 compatibility range while its v2 update wording broadly mentions all versions. Do not infer Python 3.13 SDK support from that ambiguous note or from our offline suite. The same page records a past get-last-message deadlock fix; our callback path does not justify switching to polling or blaming the historical zero-callback case on that different interface.

No measured latency win, dependency reduction or safety improvement was found that justifies replacing the current architecture. Retain the present validation-heavy research path and latest-only handoff. New functionality stays gated; external search is evidence collection, not authorization to run or import a project.

### Windows/Python and cross-domain evidence

| Question | Source / version / disposition | Finding and decision |
|---|---|---|
| Is the old Event.wait bug still present in our interpreter? | [CPython #85471](https://github.com/python/cpython/issues/85471), 2020-07-14, fixed/closed 2021-09-24; [3.10 backport #26580](https://github.com/python/cpython/pull/26580), merged 2021-06-20, `8673b77e251e42874501a47b1df86c6bde4fe1d2`; [v3.10.11 source](https://github.com/python/cpython/blob/v3.10.11/Python/thread_nt.h) | Relevant historical timeout-recalculation bug, but the tagged version already uses `_PyTime_GetPerfCounter()`. REJECT the hypothesis that this specific unfixed bug explains our 3.10.11 result. This does not eliminate ordinary OS wake latency or our former loop's accumulated delay. |
| Would upgrading Python automatically fix Event.wait? | [#89592](https://github.com/python/cpython/issues/89592), [PR #29203](https://github.com/python/cpython/pull/29203), merged 2021-11-16, `55868f1a335cd3853938082a5b25cfba66563135` | High-resolution waitable-timer work targets `time.sleep()` in 3.11, not our current Event.wait path. DEFER runtime/timer replacement; distinguish waiting API and exact version instead of treating all waits as sleep. CPython source is PSF-licensed; no code copied. |
| Can GIL reacquisition delay a ready thread? | [#52194 / bpo-7946](https://github.com/python/cpython/issues/52194), opened 2010-02-16, closed 2021-01-02 as wont-fix; [Python 3.10 switch interval docs](https://docs.python.org/3.10/library/sys.html#sys.setswitchinterval) | The old issue describes I/O/CPU contention, not a demonstrated current local fault. Documentation says the interval is ideal rather than a maximum and scheduling belongs to the OS. Supports the existing artificial-contention mechanism only; historic Live 20.05ms attribution remains UNVERIFIED. No GIL/switch-interval/worker-count change. |
| Do precise clocks guarantee prompt wake? | Microsoft [SleepConditionVariableSRW](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-sleepconditionvariablesrw), update 2025-10-31; [timeBeginPeriod](https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod), update 2024-02-22 | Timeout units, lock reacquisition and predicate rechecking are distinct from timestamp precision. Timer-resolution policy differs on newer Windows and has scheduling/power effects; it does not improve QPC precision. Do not assert CPython necessarily uses SRW: its tagged conditional implementation has multiple branches. No global timer/priority setting changes justified. |
| Is latest-frame notification a useful external pattern? | [DXcam 0.3.0](https://github.com/ra1nty/DXcam/tree/1e595ff55e57263c4b5d0414828f74104afa86f4), commit 2026-03-18, Python >=3.10; [capture loop](https://github.com/ra1nty/DXcam/blob/1e595ff55e57263c4b5d0414828f74104afa86f4/dxcam/core/capture_loop.py), [timer](https://github.com/ra1nty/DXcam/blob/1e595ff55e57263c4b5d0414828f74104afa86f4/dxcam/util/timer.py) | Latest-frame storage and Event notification are separate. Its timer advances deadlines but re-bases after sufficient lateness, unlike our phase-preserving skip. CONFIRMED source pattern, not equivalent buffer semantics or a measured win here. Retain the existing small handoff; reject ring-buffer/video stale-frame reuse and timer-library transplantation. |

DXcam's inspected repo is non-archived with 2026 source activity and [MIT license](https://github.com/ra1nty/DXcam/blob/1e595ff55e57263c4b5d0414828f74104afa86f4/LICENSE); its tests/performance were not executed here. CPython's fixed issue, merged backport and exact release source are stronger version evidence than a generic "Windows Python jitter" search result. Microsoft API documentation is used as specification reference, not OS implementation source or a redistribution grant.

### Result and gate

- External Research Gate: official docs checked; public GitHub implementations checked; relevant open/closed issues and merged/unmerged PRs checked; dated revisions/releases checked; relevant repository licenses checked. This documents a bounded comparison, not an exhaustive audit of every upstream dependency or legal terms.
- Proposed design changes: **none adopted**. The comparisons support existing separation of input, latest handoff, FK, representation and actual-avatar calibration. No quantitative outside result establishes a benefit sufficient to replace the verified implementation.
- Next useful experiment remains the already-gated single controlled cue after renewed user readiness and a fresh Safe Point. When profiling resumes for an actual new problem, use exact API/version evidence above rather than repeating fixed-bug explanations or adding timer workarounds blindly.
- Documentation-only verification: review references and privacy/provenance, check Git diff. No unchanged three-version suite or benchmark rerun is needed; previous results are not promoted to new Live evidence. Permanent policy is in `RESEARCH_FIRST_ENGINEERING.md`, linked by `AGENTS.md`, with accepted decision D-032.
