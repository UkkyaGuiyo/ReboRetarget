# Live ReboCap Adapter Safety Protocol

Status: **PHASE 2E UNVERIFIED / AUTONOMOUS RECOVERY AUTHORIZED WITH GATES**

Latest user authority: `AUTONOMOUS_ENGINEERING_AUTHORITY.md` permits at most three sequential bounded retries in one recorded Phase 2E investigation cycle, after offline recovery tests and review. Each retry requires a code change or new hypothesis; there is no reconnect loop. The Safe Point requires the same running ReboCap process, VRChat zero, SteamVR zero, and no ReboCap setting/calibration change. Existing Virtual Desktop Service/Streamer and established TCP connections are allowed and must be left unchanged. Their existence alone is not a blocker or FAIL.

This is the preflight and evidence contract for short Phase 2E receive-only validation. The first authorized run opened and closed successfully but received zero callbacks; the second was aborted without an aggregate. See `LIVE_REBOCAP_ADAPTER_VALIDATION_REPORT.md` and `PHASE_2E_RETRY_REPORT.md`. These historical outcomes do not prove the current SDK state. VRChat crashed during an earlier additional-SDK-client observation; causality remains unresolved.

## Evidence labels

- **CONFIRMED:** directly observed in this run or established by a cited official source.
- **INFERRED:** a conclusion drawn from confirmed evidence, with the inference stated.
- **UNVERIFIED:** not observed or not specified by an authoritative source. Absence of evidence is not confirmation.

## Hard Safe Point

Every item must be confirmed immediately before a future connection:

- ReboCap is already running with its protected process identity preserved; no configuration/calibration operation is required.
- VRChat is not running.
- SteamVR is not running.
- The standing-permission cycle has attempts remaining and this attempt has a documented change/new hypothesis.
- Offline-tested child isolation, aggregate recovery, and parent hard deadline are present.

Codex may inspect process state read-only. It must not create this state by starting, stopping, restarting, foregrounding, or configuring an application. Virtual Desktop background processes/connections are recorded and permitted. Unknown visible skeleton/calibration/broadcast state remains UNVERIFIED; do not operate calibration or infer that a listener proves Pose output.

## Fixed boundaries

- Use one external SDK client only. Multi-client behavior is **UNVERIFIED**, deferred, and requires separate opt-in approval.
- Use only an endpoint explicitly verified for this run. Do not scan ports, probe alternatives, or guess an incremented port.
- Load the official SDK only from a separately obtained, explicitly supplied local path. Do not discover broadly, copy, bundle, edit, or commit the SDK or its files; do not record the local path in repository artifacts.
- ReboRetarget code performs no OSC send, UDP send, or direct socket send. The sole future-authorized communication is the official SDK wrapper's documented receive-client connection to the verified endpoint. No sender, raw socket API, or packet transport is added.
- Do not change any VR application, ReboCap setting, calibration, native-output state, UI, tracker, or device state. Starting the owned probe child and terminating only that child on timeout are the explicit exceptions.
- Do not retain or write raw Pose values. The capacity-one handoff may hold only the current in-memory value during the run and must clear it on invalidation/close. Persist only aggregate counts, timings, and sanitized pass/fail evidence.
- Do not automatically reconnect. Do not run Phase 2F body-motion validation or contact VRChat, SteamVR, Virtual Desktop, or Quest.
- Maximum total supervised attempt time is 60 seconds, with a shorter observation and reserved cleanup time. There is no automatic extension; an unverified termination is not PASS.

## Preflight checklist

Record each item as `CONFIRMED`, `INFERRED`, or `UNVERIFIED`; every required item must be `CONFIRMED` before connection.

1. Standing permission has not been withdrawn, fewer than three attempts were used in this cycle, and a changed code path/new hypothesis is recorded.
2. ReboCap is already running with protected process identity; calibration and settings remain untouched. Record broadcast/calibration state without guessing.
3. VRChat and SteamVR are absent by read-only process inspection.
4. Virtual Desktop state is recorded separately and left unchanged; its processes/connections do not veto the revised gate.
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
6. Close only this SDK client at normal completion or an earlier abort. Parent deadline covers import/construction/open/observation/close; on timeout terminate only the owned child and retain partial aggregate/checkpoint evidence. Do not clean up, restart, or repair any application.

## Immediate aborts

Abort on the first occurrence of any of these conditions:

- VRChat or SteamVR starts, or the user begins VR activity.
- The official SDK reports an error or abnormal close.
- A Pose does not contain exactly 24 rotations.
- Any Pose component is non-finite, or any Quaternion is outside the predeclared unit tolerance.
- A source or receive timestamp regresses.
- The latest accepted value exceeds the predeclared stale threshold.
- ReboCap or another observed scoped process crashes or exits unexpectedly.
- The user begins VR activity, withdraws permission, or asks Codex to stop.
- Endpoint, client ownership, process/session state, data meaning, or safety becomes ambiguous.

Abort closes this SDK client and clears its in-memory latest value when responsive; the parent may terminate only its owned child on timeout or safety withdrawal. Record the sanitized reason and whether cleanup completed. Never stop, restart, foreground, configure, or otherwise clean up an application. Never reconnect automatically.

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
Phase 2E run: NOT RUN | PASS | FAIL | UNVERIFIED | ABORTED
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

## Recovery authority

The pure/offline capacity-one latest-pose state primitive is complete. Fix and regression-test the documented clock and lifecycle gaps, run independent review, then use only the bounded standing permission defined in `AUTONOMOUS_ENGINEERING_AUTHORITY.md` when its gate holds. Record attempt usage and evidence in the recovery report. Phase 2F-A remains separately unauthorized and blocked on Phase 2E PASS. No recovery work authorizes OSC output or VR application operations.
