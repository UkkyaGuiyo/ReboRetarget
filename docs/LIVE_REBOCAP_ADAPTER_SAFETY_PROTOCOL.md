# Live ReboCap Adapter Safety Protocol

Status: **NOT AUTHORIZED TO EXECUTE / WAITING_FOR_USER**

This is the preflight and evidence contract for a future, short Phase 2E receive-only validation. It is not an executable script and grants no permission to touch a live system. VRChat crashed during the earlier additional-SDK-client observation; whether that client contributed to the crash remains unresolved.

## Evidence labels

- **CONFIRMED:** directly observed in this run or established by a cited official source.
- **INFERRED:** a conclusion drawn from confirmed evidence, with the inference stated.
- **UNVERIFIED:** not observed or not specified by an authoritative source. Absence of evidence is not confirmation.

## Hard Safe Point

Every item must be confirmed immediately before a future connection:

- ReboCap is already running and calibrated by the user.
- VRChat is not running.
- SteamVR is not running.
- No active VR session exists.
- The user explicitly authorizes this one bounded run after seeing the preflight result.

Codex may inspect process state read-only. It must never create this state by starting, stopping, restarting, foregrounding, or configuring an application. A Virtual Desktop background service is not by itself an active VR session, but it is evaluated separately; if service state, headset/session state, or any other prerequisite is ambiguous, the run fails closed and does not connect.

## Fixed boundaries

- Use one external SDK client only. Multi-client behavior is **UNVERIFIED**, deferred, and requires separate opt-in approval.
- Use only an endpoint explicitly verified for this run. Do not scan ports, probe alternatives, or guess an incremented port.
- Load the official SDK only from a separately obtained, explicitly supplied local path. Do not discover broadly, copy, bundle, edit, or commit the SDK or its files; do not record the local path in repository artifacts.
- ReboRetarget code performs no OSC send, UDP send, or direct socket send. The sole future-authorized communication is the official SDK wrapper's documented receive-client connection to the verified endpoint. No sender, raw socket API, or packet transport is added.
- Do not change any VR, process, ReboCap setting, calibration, native-output state, UI, tracker, or device state.
- Do not retain or write raw Pose values. The capacity-one handoff may hold only the current in-memory value during the run and must clear it on invalidation/close. Persist only aggregate counts, timings, and sanitized pass/fail evidence.
- Do not automatically reconnect. Do not run Phase 2F body-motion validation or contact VRChat, SteamVR, Virtual Desktop, or Quest.
- Maximum connected observation time is 60 seconds. There is no automatic extension.

## Preflight checklist

Record each item as `CONFIRMED`, `INFERRED`, or `UNVERIFIED`; every required item must be `CONFIRMED` before connection.

1. User authorization identifies one run and has not been withdrawn.
2. ReboCap is already running and the user confirms action calibration is complete.
3. VRChat and SteamVR are absent by read-only process inspection.
4. The user confirms no active VR session; Virtual Desktop background-service state is recorded separately.
5. A single-client test is possible without displacing an existing external SDK client.
6. The exact endpoint and official SDK local path were supplied and verified without scanning; neither local value is committed or copied.
7. The 60-second limit, stale threshold, Quaternion unit tolerance, and abort observer are fixed in the run record before connection.
8. The output path ends at in-memory OSC representation encode/decode; no sender or direct socket call is reachable.

Any `UNVERIFIED`, conflicting, or ambiguous prerequisite means no connection.

## Bounded execution

1. Reconfirm the Hard Safe Point and authorization without changing system state.
2. Open exactly one official SDK client to the verified endpoint and request the already-established Pose contract.
3. For each callback, validate exactly 24 finite Quaternions, the predeclared unit tolerance, finite Pelvis translation, and source/receive timestamp order before accepting it.
4. Pass only the newest valid value through the live adapter, target FK, semantic anchors, VRChat representation, and OSC encode/decode in memory. A capacity-one handoff overwrites older work; it never queues a backlog.
5. Measure callback and accepted-value counts, timestamp monotonicity, overwrite/drop counts, invalidation behavior, and end-to-end processing p50/p95/p99. Do not log a Pose or Euler/position stream.
6. At 60 seconds or an earlier abort, close only this SDK client, clear the latest value, and stop. Do not clean up, restart, or repair any application.

## Immediate aborts

Abort on the first occurrence of any of these conditions:

- VRChat, SteamVR, or another unexpected scoped process starts, or an active VR session appears.
- The official SDK reports an error or abnormal close.
- A Pose does not contain exactly 24 rotations.
- Any Pose component is non-finite, or any Quaternion is outside the predeclared unit tolerance.
- A source or receive timestamp regresses.
- The latest accepted value exceeds the predeclared stale threshold.
- ReboCap or another observed scoped process crashes or exits unexpectedly.
- The user begins VR activity, withdraws permission, or asks Codex to stop.
- Endpoint, client ownership, process/session state, data meaning, or safety becomes ambiguous.

The only abort action is to close this SDK client immediately, clear its in-memory latest value, and record the sanitized reason. Never stop, restart, foreground, configure, or otherwise clean up an application. Never reconnect automatically.

## Acceptance gate

One authorized run passes only if all evidence below is `CONFIRMED`:

- Valid live values traverse SDK callback -> live delta adapter -> Target FK -> eight semantic anchors -> VRChat OSC representation -> OSC memory encode/decode, with no OSC/UDP/direct socket send.
- The capacity-one handoff exposes only the newest valid Pose, demonstrates overwrite/drop rather than backlog playback, and never accepts an older timestamp over a newer value.
- Source and receive timestamps remain monotonic for every accepted value.
- A controlled local invalidation input clears the current value. Static inspection, or a callback invocation that does not force a transport failure, confirms that the official SDK abnormal-close callback is wired to the same invalidation path. An external disconnect is not required for this gate.
- End-to-end in-memory processing p50, p95, and p99 are reported with sample count and measurement boundary.
- The client closes at or before 60 seconds; no raw Pose is retained; no application, process, setting, calibration, native output, UI, or VR session is changed.

Never force an application, transport, or network failure to observe a disconnect. If an SDK abnormal close occurs naturally, abort immediately as specified above. If none occurs, record external disconnect observation as `UNVERIFIED / NOT OBSERVED`; that fact alone does not fail an otherwise successful run. Passing this gate does not authorize multi-client testing, Phase 2F body-motion execution, VRChat startup, OSC/UDP transmission, or automatic reconnect.

## Result template

```text
Phase 2E run: NOT RUN | PASS | FAIL | ABORTED
Authorization: CONFIRMED | UNVERIFIED
Hard Safe Point: CONFIRMED | UNVERIFIED (Virtual Desktop service/session recorded separately)
Client mode: single-client-first
Endpoint/path provenance: CONFIRMED | UNVERIFIED (values omitted)
Duration / accepted / overwritten / rejected: ...
24-pose, finite, Quaternion-unit checks: ...
Source/receive timestamp monotonicity and stale threshold: ...
Latest-only handoff: ...
Controlled local invalidation: ...
Abnormal-close callback wiring: ...
External disconnect natural observation: CONFIRMED | UNVERIFIED / NOT OBSERVED
Memory-only representation round trip: ...
Processing p50 / p95 / p99 / sample count / boundary: ...
Raw Pose retained: 0
OSC/UDP/direct socket sends: 0
Application/process/settings/calibration/native-output/UI changes: 0
Abort or SDK close result: ...
Evidence labels and unresolved items: ...
Multi-client: UNVERIFIED / NOT RUN
Phase 2F body-motion execution: NOT RUN
```

## Authorization required next

The pure/offline capacity-one latest-pose state primitive is complete. Actual Phase 2E execution remains `WAITING_FOR_USER`. A future request must explicitly authorize one 60-second single-client-first run after the natural Hard Safe Point is present; general permission to continue development is not authorization for live execution.
