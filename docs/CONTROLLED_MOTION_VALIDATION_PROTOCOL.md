# Controlled Motion Validation Protocol

Status: **LIVE PAUSED FOR VRC PLAY; WRAPPER OFFLINE FUNCTIONAL PASS**. The right-only permission remains unused. The preflight 30Hz/two-speech mismatch is corrected to an explicit 60Hz consumer and four speech stages, with 219 tests passing on each of Python 3.10/3.11/3.13. A representative timing rerun of the changed wrapper is deferred until after play. No further SDK connection, speech or body cue now; require renewed readiness and a fresh Safe Point later. See `PHASE_2F_A_REPORT.md`.

The approved countdown alternative does not require intermediate chat replies. Its `hold`/`neutral` markers are scheduled acquisition boundaries, never human acknowledgements. Post-session physical confirmation is separate and cannot fill missing windows. Model/tool round trips must not drive its timing-critical path. Before more body cues, the same local wrapper/supervisor must pass silent synthetic end-to-end normal/delayed/failure/hang checks with complete windows or safe non-PASS shutdown. No time limit is extended. The later right-only restart directive supplies separate authorization, not permission to run an unverified changed path.

The user explicitly authorized Phase 2F-A and subsequently approved one motion per session, a total maximum of 60 seconds per session and up to 20 seconds for each operator response. This supersedes the old single-session-all-cues and 90-callback response limits. Phase 2F-A checks known comfortable motions against ReboCap values in memory; it does not authorize VRChat use or prove avatar, FBT, IK, sensor ownership, or product acceptance.

## Separate authorization and Safe Point

Every prerequisite must be `CONFIRMED` immediately before connecting:

- Phase 2E has passed on the same ReboCap build, coordinate mode, adapter revision, and safety boundary.
- The user's explicit Phase 2F-A authorization remains active; Phase 2E permission alone is insufficient.
- ReboCap is already running and action-calibrated by the user. Codex did not create this state.
- VRChat and SteamVR are not running and the user is performing the agreed safe motions without headset use. Virtual Desktop Service/Streamer and existing connections are permitted environmental variables and must be left untouched.
- The area and the user's condition are safe for gentle movement. A chair or other stable support is available for the left-knee cue.
- The official SDK path and endpoint are explicitly supplied and verified without copying, bundling, scanning, probing, or guessing.
- The coordinate mode, source bind, Target fixture, tracker anchors, slot mapping, stale threshold, Quaternion tolerance, baseline calculation, response multipliers, dominance checks, and conservative detectable-response floors are fixed in the run record before connection.

Codex may inspect process state read-only but must not start, stop, restart, foreground, configure, or calibrate an application to create the Safe Point.

## Fixed run boundary

- One motion per session, one official SDK client, at most 60 total supervised seconds including startup/cleanup. Normal close and owned-child exit must be confirmed before another session; no automatic reconnect loop or parallel client. Calibration and settings are untouched by Codex.
- Stop issuing new motion cues at 45 seconds. Use the remaining time only to return to neutral, collect a final neutral aggregate if safe, close this SDK client, clear temporary state, and stop.
- No extension, automatic reconnect, overlapping second client, forced application disconnect, OSC/UDP/direct output send, VR application contact, native-output change, setting change, calibration, UI automation, tracker creation or Phase 2F-B execution. Parent may terminate only its own stuck probe child under the existing watchdog; such a session is not PASS and does not automatically authorize the next connection.
- Use the capacity-one latest-pose handoff. Never queue or replay a backlog.
- Retain bounded aggregates only. Do not persist raw Pose values, per-frame time series, absolute timestamps, endpoint/path values, message bytes, identifiers, or personal motion data.

If the cutoff prevents completion, report the remaining cues as `SKIPPED / UNVERIFIED`; do not rush, extend, or reconnect.

## Cue clock and sample windows

- Record each cue and user marker with the same `receive_monotonic` clock used by the callback boundary. The sample boundary is the first accepted sequence whose `receive_monotonic >= cue_monotonic`.
- Use source timestamp only for source ordering and source-interval aggregates. Never subtract a source timestamp from a cue or receive timestamp and never treat them as one clock domain.
- Collect 60 processed latest sequences for the initial static reference, 20 for each target hold, and 20 for each return-neutral hold.
- The operator target marker must arrive within 20 seconds after the accepted move command; the neutral marker within 20 seconds after the accepted return command. This is the user's explicitly approved replacement for the old approximately 1.5-second/90-callback constraint. A timeout yields UNVERIFIED; do not manufacture a marker.
- Processed sequence numbers must increase strictly. Missing numbers count as overwrite/drop evidence; they never cause FIFO replay.

These sample windows do not override the 45-second stop-new-cues cutoff or the 60-second close limit. If a window cannot finish safely in time, leave it incomplete.

## User-paced cue sequence

Begin with a comfortable front-facing neutral baseline. Each cue may be skipped for any reason. Motions are deliberately self-selected rather than prescribed as fixed angles or distances.

1. Neutral baseline: face forward, stand naturally, stay still for 2–3 seconds and until baseline collection is acknowledged.
2. Move right without turning; hold comfortably, then return when instructed.
3. Move forward without turning; hold, then return.
4. Shallow comfortable crouch, feet grounded; hold, then return.
5. Left-knee bend with stable support or seated; do not balance unsupported.
6. Right-knee bend under the same safety rule.
7. Whole-body yaw left by a comfortable approximately 30–45 degrees; not head-only.
8. Whole-body yaw right under the same rule.
9. Raise the left arm forward comfortably below shoulder height if preferred.
10. Raise the right arm forward.
11. Move only the left shoulder gently forward without a large arm swing.
12. Move only the right shoulder forward.

Each motion is attempted once. The newer user instruction permits at most one repeat of an ambiguous cue after safe evaluation; it does not require repeating successful cues. Baseline is reacquired per session. Main agent delivers one movement at a time, confirms target hold before its window and neutral return before the return window, and never asks the user to rush for the deadline.

Nominal yaw describes an understandable cue, not a required measured angle or correctness proof. The same rule applies to every self-selected displacement and joint motion.

Immediately stop cues and abort if the user reports or shows pain, discomfort, imbalance, dizziness, fatigue, fall concern, uncertainty, or ambiguity. User safety and an unambiguous neutral return take priority over completing the list.

## Memory-only observations

For every accepted latest value, validate the existing path only in memory:

```text
official SDK value
-> ReboCap delta adapter
-> Canonical Source Pose
-> Target FK
-> eight semantic anchors
-> VRChat OSC representation
-> OSC encode/decode in memory
```

Record aggregate evidence for:

- exactly 24 finite unit-tolerance Quaternions and finite Pelvis translation;
- strictly increasing accepted receive/source timestamps and overwrite rather than backlog behavior;
- `sdk_delta * bind_global`, local/global Quaternion reconstruction, Target rest-length FK invariants, eight exact-once semantic roles, and sixteen unique memory-only messages;
- right/up/forward translation signs against the documented `+X/+Y/+Z` convention;
- yaw handedness from a rotated forward basis vector, not an Euler component;
- affected joint groups, side selection, qualitative direction, neutral return, agreement if the one permitted ambiguity repeat is used, and any ambiguity;
- Quaternion/VRChat Euler reconstruction and `q/-q` rotation equivalence, without requiring equal Euler components.

Expected observations are qualitative checks against the predeclared baseline-derived thresholds:

| Cue | Expected aggregate observation |
|---|---|
| Static | Finite baseline noise, Quaternion step, and root-drift aggregates establish the response thresholds. |
| Root right | Pelvis X change is positive and dominates horizontal Z; the same translation propagates through Target joints and anchors. |
| Root forward | Pelvis Z change is positive and dominates horizontal X. |
| Yaw left/right | For `q_relative = q_hold * inverse(q_front)`, rotating the forward `+Z` basis turns toward `-X` for left and `+X` for right; judge handedness from the basis vector, not the nominal angle. |
| Crouch | Pelvis Y decreases and reverses on return; bilateral Hip/Knee rotation response is detectable. Foot contact is not required or inferred. |
| Left knee | Left Knee local motion dominates the right-side comparator and propagates to the Left Knee/Foot anchors. |
| Left shoulder forward | Collar or Shoulder response exceeds baseline and propagates to the Left Upper Arm anchor, without identifying the owning sensor. |
| Left arm raise | Left Shoulder/Upper Arm response and upward Left Upper Arm anchor change exceed their baseline/right-side comparators. |

No listed direction, dominance, or propagation rule assigns sensor ownership, proves an independent anatomical degree of freedom, or supplies optical ground truth.

## Threshold and interpretation rule

The threshold formula, baseline window, noise statistic, multiplier, dominance rule, and each absolute floor must be declared before connection. Response thresholds are computed from the neutral-baseline noise. An absolute floor may only be a conservative lower bound for calling a response detectable; it is not a requested body displacement, target angle, anatomical truth, or correctness proof.

A cue supports its semantic check only when the aggregate response clears the declared detectable threshold, has an unambiguous sign/dominance and returns toward neutral. Report observed axis/sign separately from agreement with the expected Unity convention. An allowed repeat must support the same conclusion; disagreement remains UNVERIFIED.

A weak, below-threshold, or response-ambiguous result after an otherwise safe completed cue is `UNVERIFIED`, not proof of an SDK failure. A completed, unambiguous trial with a detectable response that contradicts a predeclared sign/dominance rule, or a value that violates an existing adapter/FK/anchor/codec invariant, is `FAIL`. `FAIL` means this gate did not validate the path; it does not by itself identify the SDK or any other component as the cause. A skipped cue is `SKIPPED / UNVERIFIED`; execution or safety ambiguity aborts the run. Do not infer sensor ownership, an independent anatomical degree of freedom, physical shoulder-tracker presence, anatomical correctness, calibrated tracker accuracy, or production suitability from correlated joint activity.

## Evidence and persistable aggregates

Use result statuses `PASS`, `FAIL`, `UNVERIFIED`, `INCOMPLETE`, and `ABORTED`. Label each reported conclusion `CONFIRMED`, `PROBABLE`, or `UNVERIFIED`. `CONFIRMED` requires direct known-action evidence; `PROBABLE` states a limited numerical inference and `UNVERIFIED` identifies insufficient or absent evidence. The automated analyzer does not promote a numerical check to physical confirmation.

Only the following bounded aggregate form may be persisted; this is a documentation contract, not a request to create a schema file or logger:

```text
schema: reboretarget.phase2f-a.aggregate.v1
run_status: PASS | FAIL | UNVERIFIED | INCOMPLETE | ABORTED
evidence_labels: CONFIRMED | PROBABLE | UNVERIFIED
limits:
  max_connected_seconds: 60
  stop_new_cues_seconds: 45
  static_processed_latest: 60
  target_hold_processed_latest: 20
  neutral_hold_processed_latest: 20
  marker_max_wait_seconds: 20
counts:
  callback / accepted / processed / overwritten / rejected
aggregate_numeric_fields:
  fixed-bin histogram / count / mean / min / max / p50 / p95 / p99
aggregate_quaternion_fields:
  hemisphere-aligned Quaternion aggregate only
trials[]:
  cue / repeat / marker status / processed count
  bounded aggregate fields / sign / dominance / neutral return
  adapter / FK / anchor / Euler / q-sign invariant result
  result: PASS | FAIL | UNVERIFIED | INCOMPLETE | ABORTED
  evidence: CONFIRMED | PROBABLE | UNVERIFIED
privacy:
  raw_pose_frames_written: 0
  raw_time_series_written: 0
  message_bytes_written: 0
  absolute_timestamps_written: 0
  endpoint_or_sdk_path_written: 0
  identifiers_written: 0
external_effects:
  osc_udp_direct_socket_sends: 0
  vr_headset_application_operations: 0
  settings_calibration_native_output_changes: 0
```

Do not persist a Pose array, per-frame sample, cue/receive/source absolute timestamp, message byte string, local endpoint, SDK path, device/account identifier, or free-form motion trace. Numeric summaries are limited to fixed-bin histogram, count, mean, min, max, p50, p95, and p99; Quaternion summaries are hemisphere-aligned aggregates only.

## Immediate aborts

Abort on the first occurrence of:

- user stop, pain, discomfort, imbalance, dizziness, fatigue, fall concern, uncertainty, or ambiguity;
- headset use, an active VR session, VRChat/SteamVR start, or unexpected scoped-process change;
- SDK error or abnormal close, non-24 Pose, non-finite value, Quaternion tolerance violation, timestamp regression, or stale input;
- loss of the declared configuration, cue/receive-time association, client ownership, Safe Point, or any safety fact;

On abort, issue no more cues, help the user remain or return neutral only if they choose and it is safe, close only this SDK client, clear temporary latest/aggregate state, and stop. Do not reconnect, stop/restart an application, force a disconnect, or attempt cleanup/repair.

At 60 seconds, close the SDK client and stop even if no safety abort occurred. If required work remains, classify the run as `INCOMPLETE`; never extend or reconnect.

## Result and acceptance

```text
Run: NOT RUN | PASS | FAIL | UNVERIFIED | INCOMPLETE | ABORTED
Authorization / Phase 2E prerequisite / Safe Point: ...
Connected duration / cue cutoff / SDK close: ...
Callback / accepted / overwritten / rejected counts: ...
Predeclared baseline and detectable-response rules: ...
Cue results and repeats: PASS | FAIL | SKIPPED | UNVERIFIED | INCOMPLETE
Evidence labels: CONFIRMED | PROBABLE | UNVERIFIED
Timestamp / adapter / FK / anchor / Euler / q-sign invariants: ...
Memory-only OSC poses/messages/decodes: ...
Raw Pose or time-series records retained: 0
OSC/UDP/direct socket sends: 0
VR/headset/application/settings/calibration/native-output changes: 0
Aborts, ambiguity, and interpretation limits: ...
```

Each session's `PASS` requires its one scheduled cue before the cutoff, neutral return, declared semantic checks, and every memory-path invariant to pass without an abort. A skipped or unfinished segment makes that session `INCOMPLETE`; a weak or response-ambiguous completed segment is `UNVERIFIED`. The combined Phase may be `PARTIAL` when required observations remain unresolved. A completed unambiguous detectable contradiction or invariant violation is `FAIL`, without automatically assigning fault to the SDK. Any execution or safety ambiguity aborts. Phase 2F-A PASS does not authorize Phase 2F-B, OSC transmission, VRChat startup, or VRChat acceptance testing.

## Current authorization

The latest play-priority instruction pauses the historical readiness/Live permissions below. Develop offline without new SDK clients, recording, VR operations or heavy performance measurement during play. Standard recording compatibility is separately assessed in `PLAYTIME_SAMPLING_ASSESSMENT.md`; its existence does not authorize capture or substitute for this controlled-motion gate.

The later performance directive requires offline countdown/fault validation, three-version full-suite success, measured strict pure p99 <10ms and independent scope/privacy/provenance review before renewed explicit user readiness. Do not run another body cue while these gates are pending or the user is unprepared. `countdown_motion_cue.py` uses the existing supervisor and schedules baseline/move/hold/return/neutral without chat/tool timing. Scheduled markers, speech process completion, audibility and actual physical motion are separate evidence; no automatic physical PASS. See `PERFORMANCE_INVESTIGATION_REPORT.md` for the current gate result and residual limitations.

Phase 2F-A and the one-motion-per-session/20-second-response override are explicitly authorized. Offline harness tests, independent review and each immediate read-only Safe Gate remain mandatory before Live. The user reported completing ordinary Calibration; Codex did not operate it. Record each session's actual cues/markers, aggregate findings, cleanup and missing evidence in `PHASE_2F_A_REPORT.md`. Raw frames stay only in bounded RAM and are never published. No Phase 2F-B, output send or VR application operation is authorized.
