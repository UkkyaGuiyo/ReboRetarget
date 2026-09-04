# Interface Contract

Status: **Phase 1 pre-implementation contract**
Last updated: 2026-09-04

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

The conventional hierarchy used by existing ReboCap integrations is pelvis-rooted legs, `Pelvis -> Spine1 -> Spine2 -> Spine3 -> Neck -> Head`, and `Spine3 -> Collar -> Shoulder -> Elbow -> Wrist -> Hand` on each side. The official SDK page identifies SMPL ordering and parent-relative local rotations but does not expose a normative parent array. The PoC must assert the hierarchy against known T-pose motion before solver work treats it as final.

### Shoulder tracker boundary

Collar, Shoulder, Elbow, Wrist, and Hand rotations are always represented in the 24-joint schema. The SDK does not expose a flag identifying whether optional physical shoulder trackers are worn. Their effect must be detected by a controlled live comparison or trusted user configuration; presence must not be inferred from the existence of shoulder bones alone.

### Adapter behavior required for the PoC

- Port is explicit configuration at first; no process scanning or silent port guessing.
- Reject connection/authentication errors and surface the SDK error code.
- On abnormal close, invalidate the current pose immediately and retry with bounded backoff. Do not replay queued frames.
- Keep only the newest complete pose. Do not build a backlog.
- Record receive time separately from the source timestamp until timestamp semantics are verified.
- Never trigger ReboCap calibration or change ReboCap settings automatically.

### Still unverified live

- A callback sample from the currently installed build.
- Exact timestamp unit/epoch and observed jitter/rate.
- Multiple simultaneous external SDK clients. The GUI must be running because it provides the broadcast, but multi-client support is not explicitly documented.
- The observable difference between physical shoulder trackers present and absent.

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

### Confirmed wire contract

- Transport: OSC over UDP.
- Default target: `127.0.0.1:9000`; make host and port configurable because VRChat supports a launch override.
- Body addresses: `/tracking/trackers/{1..8}/position` and `/tracking/trackers/{1..8}/rotation`.
- Optional alignment addresses: `/tracking/trackers/head/position` and `/tracking/trackers/head/rotation`.
- Each message contains three floats `(X, Y, Z)`.
- Positions are world-space Unity coordinates, left-handed, `+Y` up, with `1.0` equal to one metre.
- Rotations are Euler angles in degrees. VRChat applies them internally in `Z, X, Y` order.
- VRChat supports at most eight additional points: hip, chest, two feet, two knees, and two elbow/upper-arm points.

### Proposed deterministic sender slots

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

VRChat's OSC addresses are numbered rather than role-named. This table is ReboRetarget's stable internal ordering, not a claim that VRChat binds role by slot number. Role interpretation and body alignment are established by spatial arrangement and the VRChat FBT calibration flow.

### Alignment and calibration

- The user must enable OSC and perform VRChat `Calibrate FBT` on the actual avatar.
- A tracker worn/placed above the elbow controls elbow and shoulder together in VRChat.
- Optional head position shifts OSC tracking space to the avatar head-bone root every frame without smoothing.
- Optional head rotation controls yaw. A single message is an instant alignment; a second within 300 ms changes it to streamed mode with lerp and a 10-second timeout.
- The first PoC must compare explicit head-reference alignment with VRChat's current manual/auto-centering flow. It must not silently stream a head reference before axes and origin are validated.

### Conversion and freshness requirements

- Treat ReboCap `UnityCoordinate` as the starting convention, but verify each axis and handedness with known motion. The pelvis/root origin still needs an explicit session alignment transform.
- Convert solved global tracker quaternions to the exact Euler representation consumed by VRChat; do not send quaternion components as Euler angles.
- Send at most one update per newly accepted source pose and never replay stale frames. The initial rate ceiling is the 60 Hz source cadence; VRChat documents no required tracker rate, so actual loss/jitter must be measured.
- If input is stale, invalid, or disconnected, stop generating new tracker packets and expose the fault. The final timeout threshold is a PoC measurement, not yet a fixed constant.

### Eight-point decision

The planned eight semantic points match the current documented maximum and roles. They remain the target configuration, but transmission of all eight is evidence-gated: VRChat explicitly warns that fewer high-quality points can outperform inaccurate or drifting extra points. The PoC must compare at least hip+feet, hip+feet+knees, and the full eight-point set on the final avatar surface.

### Coexistence boundary

Official documentation says OSC trackers should function similarly to SteamVR trackers, but does not define deterministic precedence for duplicate roles from both sources. Production mode must therefore avoid duplicate ReboCap native body trackers. Quest controllers remain on the normal hand path and are not replaced by this interface.

## 4. Virtual Desktop / Quest Boundary

Virtual Desktop remains the HMD/controller transport into SteamVR. Its optional emulated body trackers use a separate driver/configuration surface and can overlap waist, chest, knees, feet, and elbows. ReboRetarget must identify those devices as external and leave their settings unchanged. Quest chest-yaw work remains the independent OFF/MONITOR-first research track; it is not part of this contract.

## 5. Acceptance Surface for the Next PoC

The next PoC is complete only when a user-authorized session demonstrates all of the following without changing protected settings:

1. The official SDK connects to the running ReboCap GUI after the user's existing calibration.
2. Live callbacks expose the documented joint count/order and plausible pelvis translation/rotations at measured cadence.
3. Known body motions verify axes, quaternion order, hierarchy, timestamp behavior, and shoulder-data behavior.
4. Disconnect/reconnect invalidates stale data and does not replay backlog.
5. No production OSC sender, retarget solver, GUI, watcher, startup integration, or automatic SteamVR-output controller has been introduced.

The subsequent OSC packet PoC is a separate gate and must be verified in VRChat, not merely by packet capture.

## 6. Sources

- ReboCap SDK interface: <https://doc.rebocap.com/en_US/SDK/>
- ReboCap connection and PC/VR controls: <https://doc.rebocap.com/en_US/ui_help_doc/control/connect.html>
- ReboCap WebSocket configuration: <https://doc.rebocap.com/en_US/ui_help_doc/control/config.html>
- ReboCap SteamVR integration: <https://doc.rebocap.com/en_US/third_party_software_access/steamvr/>
- VRChat OSC trackers: <https://docs.vrchat.com/docs/osc-trackers>
- VRChat OSC ports: <https://docs.vrchat.com/docs/osc-overview>
- VRChat full-body tracking: <https://docs.vrchat.com/docs/full-body-tracking>
- OpenVR driver/tracker roles: <https://github.com/ValveSoftware/openvr/blob/master/docs/Driver_API_Documentation.md>
