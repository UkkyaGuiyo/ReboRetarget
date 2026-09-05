# Interface Contract

Status: **Phase 2E single-client Live value path validated; output remains memory-only**
Last updated: 2026-09-05

This document defines the narrow external boundary for the first ReboRetarget proof of concept. It records confirmed behavior separately from requirements and unresolved items. It is not an implementation claim.

## 1. ReboCap Input Adapter

### Confirmed source contract

- Connect as a local WebSocket client through the official ReboCap SDK wrapper. ReboCap GUI hosts the broadcast; the documented default port is `7690`, and ReboCap may increment it if occupied.
- Pose output begins only after the user performs ReboCap action calibration.
- The documented live rate is 60 frames per second.
- Request `UnityCoordinate` and global rotations for the first PoC. The SDK also supports local rotations and several coordinate modes.
- One pose contains:
  - `trans[3]`: pelvis/root translation in metres.
  - `pose24`: 24 quaternions, documented and demonstrated as `(w, x, y, z)`.
  - `static_index`: foot/contact information.
  - timestamp: transported by the SDK, but its epoch and final unit after wrapper conversion are not documented clearly enough to treat as confirmed.
- The regular pose message contains no independent world position for every bone. Joint positions must be reconstructed from the pelvis translation, rotations, hierarchy, and a chosen skeleton/rest-pose model.
- The SDK supports a callback, abnormal-close callback, and `get_last_msg` polling.

### Joint order

The confirmed 24-joint SMPL-style order is:

1. Pelvis
2. L_Hip
3. R_Hip
4. Spine1
5. L_Knee
6. R_Knee
7. Spine2
8. L_Ankle
9. R_Ankle
10. Spine3
11. L_Foot
12. R_Foot
13. Neck
14. L_Collar
15. R_Collar
16. Head
17. L_Shoulder
18. R_Shoulder
19. L_Elbow
20. R_Elbow
21. L_Wrist
22. R_Wrist
23. L_Hand
24. R_Hand

The hierarchy is confirmed from two official code distributions: ReboCap Unity SDK v4 and ReboCap Unreal Engine plugin source v2. Both encode pelvis-rooted legs, `Pelvis -> Spine1 -> Spine2 -> Spine3 -> Neck -> Head`, and `Spine3 -> Collar -> Shoulder -> Elbow -> Wrist -> Hand` on each side. Unity uses `-1` for the root parent, while Unreal uses self index `0`; ReboRetarget normalizes the Pelvis parent to `None`. The complete normalized parent-index array is `(-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19,20,21)`.

The SDK documentation states that all output rotations are relative to T-pose. Official Unity and Unreal integration code composes each received ReboCap Quaternion with a bind/T-pose global rotation. Therefore the SDK's global values must not be treated as already-composed absolute bind rotations. Phase 2C implements the pure/offline boundary as `source_absolute_global = sdk_rotation_delta * source_bind_global_rotation`. A research-only bounded SDK probe now exercises this boundary, but no production/live client exists.

### Shoulder tracker boundary

Collar, Shoulder, Elbow, Wrist, and Hand rotations are always represented in the 24-joint schema. The SDK does not expose a flag identifying whether optional physical shoulder trackers are worn. Their effect must be detected by a controlled live comparison or trusted user configuration; presence must not be inferred from the existence of shoulder bones alone.

### Adapter behavior required for the PoC

- Port is explicit configuration at first; no process scanning or silent port guessing.
- Reject connection/authentication errors and surface the SDK error code.
- On abnormal close, invalidate the current pose immediately and do not replay queued frames. Phase 2E stops without reconnecting; any production reconnect policy remains a later design decision.
- Keep only the newest complete pose. Do not build a backlog.
- Record receive time separately from the source timestamp until timestamp semantics are verified.
- Never trigger ReboCap calibration or change ReboCap settings automatically.

`LatestPoseSlot` now implements the state portion of this contract offline. It accepts already-validated generic values and caller-supplied timestamps, stores at most one sample, requires both receive and source timestamps to advance strictly, and clears its value on stale/disconnect while preserving ordering watermarks. Payload is opaque and is neither validated nor copied: `None` may be a valid value, while Pose callers must provide an already-validated immutable value and not mutate it after publication. It uses one `threading.Lock` for atomic multi-field access but creates no thread and reads no clock. The 0.250-second threshold used in tests is a provisional Phase 2E candidate based on the observed 130.4663 ms maximum receive gap and zero gaps at least 250 ms; it is not a product default.

On 2026-09-05, the initial attempt delivered zero callbacks and a second was aborted without an aggregate; their causes remain unknown. See `PHASE_2E_RETRY_REPORT.md`. After clock and supervised-lifecycle recovery, **Phase 2E passed** on the first standing-permission cycle attempt: 1200 valid callbacks traversed Delta/Canonical/latest, 429 unique values completed Target FK/eight anchors/sixteen memory OSC messages, and the client closed with clean child exit inside 20.249216 seconds total. See [`PHASE_2E_RECOVERY_REPORT.md`](PHASE_2E_RECOVERY_REPORT.md). The cycle is complete at 1/3 attempts. The supervisor loads no vendor SDK in its parent and retains only sanitized aggregate checkpoints. Virtual Desktop background processes/connections are permitted and untouched. PASS is single-client Live value-path evidence, not avatar or active-VR coexistence proof.

### Still unverified live

- Known-action axis signs and anatomical input semantics. The T-pose-delta adapter's Live value connection is now confirmed by Phase 2E; controlled motion is not.
- Multiple simultaneous external SDK clients. The GUI must be running because it provides the broadcast, but multi-client support is not explicitly documented.
- The observable difference between physical shoulder trackers present and absent.

### Controlled-motion semantics gate

Phase 2F-A was explicitly authorized and two rightward trials were incomplete. It is now `PARTIAL / OFFLINE RECOVERY`, defined in [`CONTROLLED_MOTION_VALIDATION_PROTOCOL.md`](CONTROLLED_MOTION_VALIDATION_PROTOCOL.md). Recovery requires same-wrapper fake SDK/speech completion, fault cleanup, full multi-version tests, unchanged strict pure p99 <10ms and reviewed performance evidence before renewed user readiness and a fresh Safe Point. The single-client run is at most 60 seconds including cleanup, stops new cues at 45 seconds, retains only aggregates, and ends at OSC encode/decode in memory without output send or VR contact.

The recovery wrapper locally schedules markers; it cannot certify human motion or audibility. Its numerical outcome remains separate from physical confirmation. The research consumer targets a phase-preserving cadence, wakes on publish, skips missed deadlines and reads only the latest sample. It is not a product scheduler or hard-real-time guarantee. The immutable prepared source-bind adapter shares the defensive adapter's dynamic composition/validation semantics; external input and static bind validation remain separate. See `PERFORMANCE_INVESTIGATION_REPORT.md` for exact benchmark boundaries and unresolved Live causality.

Its thresholds are declared from neutral-baseline noise before cues, with any absolute floor serving only as a conservative detectable-response floor. Fixed displacement or angle is not correctness evidence. Weak, below-threshold, or response-ambiguous data remains `UNVERIFIED`; an unambiguous detectable contradiction or deterministic invariant violation is `FAIL`, without attributing fault to the SDK. Correlated motion does not prove sensor ownership, independent degrees of freedom, physical shoulder-tracker presence, anatomical correctness, or product suitability. Phase 2F-A PASS validates only the controlled ReboCap value path and does not authorize or satisfy VRChat acceptance.

## 2. SteamVR Native Output Controller

### Confirmed installed surface

- ReboCap installs an OpenVR driver named `rebocap` under SteamVR's driver directory.
- Its input profiles declare `TrackedDeviceClass_GenericTracker` and cover waist, chest, knees, ankles, feet, shoulders, elbows, wrists, and an unassigned role.
- Historical local driver logs show ReboCap devices appearing as OpenVR device class 3 (`GenericTracker`). No device serials or raw logs are stored in this repository.
- The official ReboCap UI has a PC-side advanced `VR Output` switch and a VR-panel node selector. The installed configuration contains names corresponding to PC VR output, VR output nodes, AI Engine, Ground IK, sensor/skeleton/calibration, and other protected settings.

### Control status

**No supported, safely reversible programmatic master switch has been confirmed.** The public SDK exposes pose acquisition and connection functions, not SteamVR-output control. No dedicated ReboCap registry value was found. Internal inspection found configuration/UI symbols and named-pipe communication, but not a supported external command with query/set/acknowledgement semantics.

The installed `config.data` is a custom/pickle-derived binary store containing the candidate output key alongside many unrelated user settings. Direct rewriting is rejected because it could clobber shoulder assignment, sensor mapping, calibration, AI Engine, Ground IK, or other state, and because concurrent ReboCap writes are possible.

### Required controller contract before production implementation

- `read_state()` must return an observed state, not a default assumption.
- `disable_native_body_output()` may change only the confirmed native body-output switch and must receive an acknowledgement/readback.
- `restore(previous_state)` must restore exactly what `read_state()` observed, including an originally-OFF state.
- Crash recovery must store only the minimum pending restoration fact and re-check ownership/current state before writing.
- If state cannot be read or the switch is ambiguous, fail closed: emit no production OSC and ask for manual action.
- Node assignments and every protected ReboCap setting are outside this interface.

### Phase 2/PoC rule

Until the switch is proven in a user-authorized A/B session, the minimal Pose PoC must not edit `config.data`, call undocumented IPC, or manipulate ReboCap UI. Any VRChat output test must use an explicitly confirmed manual native-output-OFF state or run without a conflicting live SteamVR/VRChat path.

## 3. VRChat OSC Output

### Offline semantic-transform and representation boundary

Phase 2C produces immutable Quaternion tracker transforms for exactly Hip, Chest, both Knees, both Feet, and both Upper Arms. Each is defined by a target joint, local position offset, and local rotation offset. Position uses `joint_position + rotate(joint_rotation, local_position_offset)` and rotation uses `joint_rotation * local_rotation_offset`. The supplied offsets are replaceable synthetic fixtures, not product defaults.

Phase 2D maps those semantic roles through separate configurable slot data, passes the synthetic metre/Unity-axis positions unchanged, converts Quaternion to the current VRChat Euler convention only at the representation boundary, and encodes/decodes the required OSC message subset in memory. `reboretarget/vrchat_osc.py` has no socket, sender, network, process, filesystem, clock, or live-SDK access.

### Confirmed wire contract

- Transport: OSC over UDP.
- Default target: `127.0.0.1:9000`; make host and port configurable because VRChat supports a launch override.
- Body addresses: `/tracking/trackers/{1..8}/position` and `/tracking/trackers/{1..8}/rotation`.
- Optional alignment addresses: `/tracking/trackers/head/position` and `/tracking/trackers/head/rotation`.
- Each message contains three floats `(X, Y, Z)`.
- Positions are world-space Unity coordinates, left-handed, `+X` right, `+Y` up, `+Z` forward, with `1.0` equal to one metre.
- Rotations are Euler angles in degrees. VRChat applies fixed-world-axis rotations in `Z, X, Y` order; in the repository's Hamilton active convention the equivalent reconstruction is `qY * qX * qZ`.
- VRChat supports at most eight additional points: hip, chest, two feet, two knees, and two elbow/upper-arm points.

### Implemented deterministic representation slots

| Slot | ReboRetarget semantic point |
|---:|---|
| 1 | Hip |
| 2 | Chest |
| 3 | Left Knee |
| 4 | Right Knee |
| 5 | Left Foot |
| 6 | Right Foot |
| 7 | Left Upper Arm / elbow control point |
| 8 | Right Upper Arm / elbow control point |

VRChat's OSC addresses are numbered rather than role-named. This table is ReboRetarget's default internal transport ordering, held as validated replaceable data, not a claim that VRChat binds role by slot number. All eight semantic roles and slots 1 through 8 must occur exactly once. Role interpretation and body alignment are established by spatial arrangement and the VRChat FBT calibration flow.

### Alignment and calibration

- The user must enable OSC and perform VRChat `Calibrate FBT` on the actual avatar.
- A tracker worn/placed above the elbow controls elbow and shoulder together in VRChat.
- Optional head position shifts OSC tracking space to the avatar head-bone root rather than the eye position. Current documentation describes continuous position alignment without smoothing, and the 2026.1.2 release notes add an immediate one-pulse position snap.
- Optional head rotation controls yaw. A single message is an instant alignment; a second within 300 ms changes it to streamed mode with lerp and a 10-second timeout.
- The official sources do not assign the head-rotation 300 ms/10-second thresholds to head position. Sender timing and single-shot/stream selection remain future behavior rather than packet fields and must not be inferred across the two endpoints.
- A future live-output PoC must compare explicit head-reference alignment with VRChat's current manual/auto-centering flow. It must not silently stream a head reference before axes and origin are validated.

### Conversion and freshness requirements

- Treat ReboCap `UnityCoordinate` as the starting convention, but verify each live axis and handedness with known motion. The pelvis/root origin still needs an explicit session alignment transform. Phase 2D adds no output-layer inversion or scale to its already-Unity-labelled synthetic positions.
- Phase 2D keeps solved tracker rotations as Quaternion until the output boundary and converts to degree Euler for fixed `Z -> X -> Y` application. Tests reconstruct the Quaternion and compare rotation equivalence rather than Euler components; singular branches may be discontinuous while remaining finite and equivalent.
- The offline Source-to-VRChat tracking-space alignment is a separate rigid transform: `position' = yaw * position + translation`, `rotation' = yaw * rotation`. It applies uniformly to all eight points and is not a recenter implementation.
- Send at most one update per newly accepted source pose and never replay stale frames. The initial rate ceiling is the 60 Hz source cadence; VRChat documents no required tracker rate, so actual loss/jitter must be measured.
- If input is stale, invalid, or disconnected, stop generating new tracker packets and expose the fault. The final timeout threshold is a PoC measurement, not yet a fixed constant.

### Eight-point decision

The planned eight semantic points match the current documented maximum and roles. They remain the target configuration, but transmission of all eight is evidence-gated: VRChat explicitly warns that fewer high-quality points can outperform inaccurate or drifting extra points. The PoC must compare at least hip+feet, hip+feet+knees, and the full eight-point set on the final avatar surface.

### Coexistence boundary

Official documentation says OSC trackers should function similarly to SteamVR trackers, but does not define deterministic precedence for duplicate roles from both sources. Production mode must therefore avoid duplicate ReboCap native body trackers. Quest controllers remain on the normal hand path and are not replaced by this interface.

## 4. Virtual Desktop / Quest Boundary

Virtual Desktop remains the HMD/controller transport into SteamVR. Its optional emulated body trackers use a separate driver/configuration surface and can overlap waist, chest, knees, feet, and elbows. ReboRetarget must identify those devices as external and leave their settings unchanged. Quest chest-yaw work remains the independent OFF/MONITOR-first research track; it is not part of this contract.

## 5. Phase 2D Acceptance and Next Safety Gate

The Phase 2D offline gate is implemented: eight semantic Quaternion transforms become eight deterministic VRChat representation values and sixteen OSC `,fff` messages, then decode successfully in memory. Rotation-equivalent round trips cover the required axes, compounds, singularities, angle boundaries, and `q/-q`. Head alignment is a separate value model; yaw-plus-translation tracking-space alignment preserves body morphology.

The pure/offline capacity-one latest-pose primitive remains free of owned threads and SDK/process/network dependencies. The separate research **Live ReboCap Adapter Safety Validation** now passes with measured evidence in [`PHASE_2E_RECOVERY_REPORT.md`](PHASE_2E_RECOVERY_REPORT.md). The revised Safe Point, single-client-first boundary, parent watchdog, aborts and acceptance gate are in `LIVE_REBOCAP_ADAPTER_SAFETY_PROTOCOL.md`. Historical zero-callback and aborted retry reports remain evidence, not current failure status. Phase 2F-A requires separate authorization. Multi-client testing, actual UDP/OSC transmission and VR application interactions remain later gates. Actual avatar output must eventually be verified in VRChat, not by packet construction or upstream registration alone.

## 6. Sources

- ReboCap SDK interface: <https://doc.rebocap.com/en_US/SDK/>
- ReboCap Unity SDK v4: `Assets/RebocapSdk/DemoScenes/SdkManager.cs:39-64,385-389,432-433` and `Assets/RebocapSdk/RebocapWsSdk.cs:74-99`; official archive SHA-256 `E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF`.
- ReboCap Unreal Engine plugin v2: `Source/rebocap_runtime/Private/rebocap_source.cpp:115-152` and `rebocap_pose_node.cpp:282-308`; official archive SHA-256 `AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53`.
- ReboCap connection and PC/VR controls: <https://doc.rebocap.com/en_US/ui_help_doc/control/connect.html>
- ReboCap WebSocket configuration: <https://doc.rebocap.com/en_US/ui_help_doc/control/config.html>
- ReboCap SteamVR integration: <https://doc.rebocap.com/en_US/third_party_software_access/steamvr/>
- VRChat OSC trackers: <https://docs.vrchat.com/docs/osc-trackers>
- VRChat OSC ports: <https://docs.vrchat.com/docs/osc-overview>
- VRChat full-body tracking: <https://docs.vrchat.com/docs/full-body-tracking>
- VRChat IK 2.0 features and options: <https://docs.vrchat.com/docs/ik-20-features-and-options>
- VRChat 2026.1.2 release notes: <https://docs.vrchat.com/docs/vrchat-202612>
- Unity rotation conventions: <https://docs.unity3d.com/6000.0/Documentation/Manual/QuaternionAndEulerRotationsInUnity.html>
- Unity `Quaternion.Euler`: <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Quaternion.Euler.html>
- OSC 1.0 specification: <https://opensoundcontrol.stanford.edu/spec-1_0.html>
- OpenVR driver/tracker roles: <https://github.com/ValveSoftware/openvr/blob/master/docs/Driver_API_Documentation.md>
