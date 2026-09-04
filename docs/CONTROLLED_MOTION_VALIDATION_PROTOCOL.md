# Controlled Motion Validation Protocol

Status: **NOT AUTHORIZED TO EXECUTE / WAITING_FOR_USER**

This document prepares one future Phase 2F-A controlled-motion run. It does not authorize that run. Phase 2F-A checks whether known, comfortable user motions produce internally consistent ReboCap values through the existing memory-only path. A PASS proves only that controlled ReboCap value path; it neither authorizes VRChat use nor proves VRChat, avatar, FBT, IK, tracker, or product acceptance.

## Separate authorization and Safe Point

Every prerequisite must be `CONFIRMED` immediately before connecting:

- Phase 2E has passed on the same ReboCap build, coordinate mode, adapter revision, and safety boundary.
- The user explicitly authorizes this one Phase 2F-A run. Phase 2E authorization does not carry over.
- ReboCap is already running and action-calibrated by the user. Codex did not create this state.
- VRChat and SteamVR are not running; no headset is being worn or used; no active VR session exists. Virtual Desktop background-service state is recorded separately, and any session ambiguity fails closed.
- The area and the user's condition are safe for gentle movement. A chair or other stable support is available for the left-knee cue.
- The official SDK path and endpoint are explicitly supplied and verified without copying, bundling, scanning, probing, or guessing.
- The coordinate mode, source bind, Target fixture, tracker anchors, slot mapping, stale threshold, Quaternion tolerance, baseline calculation, response multipliers, dominance checks, and conservative detectable-response floors are fixed in the run record before connection.

Codex may inspect process state read-only but must not start, stop, restart, foreground, configure, or calibrate an application to create the Safe Point.

## Fixed run boundary

- One authorized run, one official SDK client, single-client-first, and at most 60 connected seconds.
- Stop issuing new motion cues at 45 seconds. Use the remaining time only to return to neutral, collect a final neutral aggregate if safe, close this SDK client, clear temporary state, and stop.
- No extension, reconnect, second client, forced disconnect, OSC/UDP/direct socket send, VR application contact, native-output change, setting change, calibration, UI automation, tracker creation, or Phase 2F-B/VRChat execution.
- Use the capacity-one latest-pose handoff. Never queue or replay a backlog.
- Retain bounded aggregates only. Do not persist raw Pose values, per-frame time series, absolute timestamps, endpoint/path values, message bytes, identifiers, or personal motion data.

If the cutoff prevents completion, report the remaining cues as `SKIPPED / UNVERIFIED`; do not rush, extend, or reconnect.

## Cue clock and sample windows

- Record each cue and user marker with the same `receive_monotonic` clock used by the callback boundary. The sample boundary is the first accepted sequence whose `receive_monotonic >= cue_monotonic`.
- Use source timestamp only for source ordering and source-interval aggregates. Never subtract a source timestamp from a cue or receive timestamp and never treat them as one clock domain.
- Collect 60 processed latest sequences for the initial static reference, 20 for each target hold, and 20 for each return-neutral hold.
- The user's target marker must arrive within 90 accepted callbacks after its move cue; the neutral marker must arrive within 90 accepted callbacks after its return cue. Otherwise stop that trial as `UNVERIFIED` and do not manufacture a boundary.
- Processed sequence numbers must increase strictly. Missing numbers count as overwrite/drop evidence; they never cause FIFO replay.

These sample windows do not override the 45-second stop-new-cues cutoff or the 60-second close limit. If a window cannot finish safely in time, leave it incomplete.

## User-paced cue sequence

Begin with a comfortable front-facing neutral baseline. Each cue may be skipped for any reason. Motions are deliberately self-selected rather than prescribed as fixed angles or distances.

1. Root shift right, once; return to neutral.
2. Root shift forward, once; return to neutral.
3. Whole-body yaw left through a comfortable approximate quarter-turn (nominally 90 degrees), once; return to neutral.
4. Whole-body yaw right through a comfortable approximate quarter-turn (nominally 90 degrees), once; return to neutral.
5. Shallow, comfortable crouch, twice; the user chooses the depth and may stop before either repeat.
6. Left-knee bend, twice, while seated or using stable support; do not balance unsupported on one leg.
7. Gentle left-shoulder-forward motion, twice; return to neutral after each.
8. Comfortable left-arm raise, twice; return to neutral after each.

The root and yaw cues have one repetition per listed direction. Only crouch, left knee, left shoulder, and left arm have two repetitions. No cue is repeated merely to manufacture a passing result.

The nominal quarter-turn describes an understandable cue, not a required measured angle or correctness proof. The same rule applies to every self-selected displacement and joint motion.

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
- affected joint groups, side selection, qualitative direction, neutral return, repeat agreement where two repeats are required, and any ambiguity;
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

A cue supports its semantic check only when the aggregate response clears the declared detectable threshold, has the expected qualitative sign/dominance, and returns toward neutral. Both repetitions must support the same qualitative conclusion for crouch, left knee, left shoulder, and left arm. Root and yaw are assessed once per listed direction.

A weak, below-threshold, or response-ambiguous result after an otherwise safe completed cue is `UNVERIFIED`, not proof of an SDK failure. A completed, unambiguous trial with a detectable response that contradicts a predeclared sign/dominance rule, or a value that violates an existing adapter/FK/anchor/codec invariant, is `FAIL`. `FAIL` means this gate did not validate the path; it does not by itself identify the SDK or any other component as the cause. A skipped cue is `SKIPPED / UNVERIFIED`; execution or safety ambiguity aborts the run. Do not infer sensor ownership, an independent anatomical degree of freedom, physical shoulder-tracker presence, anatomical correctness, calibrated tracker accuracy, or production suitability from correlated joint activity.

## Evidence and persistable aggregates

Use result statuses `PASS`, `FAIL`, `UNVERIFIED`, `INCOMPLETE`, and `ABORTED`. Label each reported conclusion `CONFIRMED`, `INFERRED`, or `UNVERIFIED`. `CONFIRMED` is direct evidence from the bounded run, `INFERRED` states a limited conclusion drawn from that evidence, and `UNVERIFIED` identifies insufficient or absent evidence.

Only the following bounded aggregate form may be persisted; this is a documentation contract, not a request to create a schema file or logger:

```text
schema: reboretarget.phase2f-a.aggregate.v1
run_status: PASS | FAIL | UNVERIFIED | INCOMPLETE | ABORTED
evidence_labels: CONFIRMED | INFERRED | UNVERIFIED
limits:
  max_connected_seconds: 60
  stop_new_cues_seconds: 45
  static_processed_latest: 60
  target_hold_processed_latest: 20
  neutral_hold_processed_latest: 20
  marker_max_accepted_callbacks: 90
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
  evidence: CONFIRMED | INFERRED | UNVERIFIED
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
Evidence labels: CONFIRMED | INFERRED | UNVERIFIED
Timestamp / adapter / FK / anchor / Euler / q-sign invariants: ...
Memory-only OSC poses/messages/decodes: ...
Raw Pose or time-series records retained: 0
OSC/UDP/direct socket sends: 0
VR/headset/application/settings/calibration/native-output changes: 0
Aborts, ambiguity, and interpretation limits: ...
```

`PASS` requires all scheduled cues before the cutoff, the required repeat pattern, neutral returns, declared semantic checks, and every memory-path invariant to pass without an abort. A skipped or unfinished segment makes the run `INCOMPLETE`; a weak or response-ambiguous completed segment is `UNVERIFIED`. A completed unambiguous detectable contradiction or invariant violation is `FAIL`, without automatically assigning fault to the SDK. Any execution or safety ambiguity aborts. Phase 2F-A PASS does not authorize Phase 2F-B, OSC transmission, VRChat startup, or VRChat acceptance testing.

## Authorization required next

Phase 2F-A remains **NOT AUTHORIZED TO EXECUTE / WAITING_FOR_USER**. The immediate project gate is still the separately authorized Phase 2E run. Only after Phase 2E passes may the user separately authorize this one controlled-motion run at a newly confirmed natural Safe Point.
