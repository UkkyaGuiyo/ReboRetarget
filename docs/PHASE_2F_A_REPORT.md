# Phase 2F-A Controlled Motion Report

Date: 2026-09-05. Status: **PARTIAL — motion semantics UNVERIFIED**.

This report preserves the historical Live attempts. The subsequent offline wrapper/performance recovery is documented in `PERFORMANCE_INVESTIGATION_REPORT.md`; its results supersede only the old untested-wrapper checkpoint, not these motion findings.

## Later right-only restart: preflight, no Live session

The user supplied the Research-First / Autonomous Cue Wrapper Edition directive and explicitly reported readiness after reattachment/calibration instructions. Read-only preflight found the protected ReboCap process and its native 3D child running, no VRChat or SteamVR process, and the existing listener with only its native 3D client in the inspected connections. Virtual Desktop was untouched. This is a time-specific inspection, not a reusable Safe Point.

Before connecting, source inspection and independent peer review found a mismatch with the new requested sequence: `run_countdown` constructed `ProbeConfig(duration_seconds=55)`, retaining the 30Hz default, and emitted only move/return speech. Initial neutral and finish were silent. The earlier G2 synthetic 58.88Hz result used a separate 60Hz configuration; earlier H wrapper success did not establish that configuration or the newly requested speech stages.

No new official SDK connection, speech or body cue was started. The user was released from holding still while a bounded offline wrapper correction was selected. The latest permission is for one right cue only; it has not been consumed. Before any eventual run, re-establish current readiness and the Safe Point rather than assuming the user stayed ready during offline work. Raw Pose saved, output sends, settings/Calibration changes and application launches remain zero for this preflight.

## Four-stage wrapper: offline functional completion

The narrow correction explicitly selects a 60Hz consumer and schedules initial-neutral, move, return and finish speech. Finish speech follows clean SDK-child exit and describes capture completion, never semantic PASS. The original total deadline, per-speech timeout and owned-child-only cleanup remain in force. The synthetic benchmark reports the actual aggregate configuration instead of labeling the wrapper from an unrelated requested-rate variable.

Existing completed full-suite results, reused without rerunning during VRC play:

| Python | Tests | Elapsed seconds | Result |
|---|---:|---:|---|
| 3.10 | 219 | 320.414 | OK, exit 0 |
| 3.11 | 219 | 318.686 | OK, exit 0 |
| 3.13 | 219 | 319.674 | OK, exit 0 |

The suites include silent fake-SDK/fake-speech 60/20/20 completion, initial/finish guidance boundaries, no-input classification, speech failures/timeouts, SDK lifecycle hangs and owned-child cleanup. Some suites overlapped as functional checks; these elapsed times are not controlled performance benchmarks. Independent Scope Guard accepted the correction and privacy/provenance review accepted its fixed allowlist/aggregate-only evidence. A subsequent read-only comparison confirmed no additional code changes after these results.

No actual speech, new Live SDK connection or body cue occurred. The changed four-stage wrapper has no new representative p99/cadence benchmark; do not transfer old two-stage H timings or separate G2 58.88Hz results to it. Real audibility, physical-right mapping and active-VR coexistence remain UNVERIFIED. The user now prioritizes VRC play: retain the correction locally, defer heavy measurement and Live work, and do not assume earlier readiness remains valid.

## Authorization and session

The user reported ordinary Calibration complete, confirmed neutral readiness, and authorized controlled known motions. The subsequent approved bounds were one motion per session, 60 total supervised seconds and 20 seconds per operator response. No application or Calibration operation was performed by Codex.

One official-SDK receive-only session attempted the `right` cue. The neutral window completed with 60 processed samples. The move marker was accepted at session elapsed 25.088477 seconds. The user subsequently acknowledged the rightward hold, but its control command did not reach the running session before the 20-second deadline. The session reached `INCOMPLETE / MARKER_TIMEOUT` at 45.131762 seconds, with **60 baseline / 0 held / 0 returned** samples. The user was told to return comfortably to neutral; that return was not measured.

The final child checkpoint was `result_ready` at 45.253682 seconds. The supervisor reported `CHILD_EXIT`, `within_deadline=true` and no termination request/error. A postflight process inspection found no remaining probe, the original protected ReboCap process alive, and zero VRChat/SteamVR processes. The complete parent duration/individual lifecycle counters were not retained in the bounded console excerpt and are not reconstructed from other timing fields.

At that checkpoint no second Live session or reconnect had been performed. This was a timing-association failure, not evidence of an incorrect user movement or incorrect physical axis. A later separately approved countdown retry is recorded below.

## Transport and pipeline aggregates

| Measure | Observed |
|---|---:|
| Callbacks received | 2700 |
| Accepted callbacks / Delta / Canonical / published latest | 2699 each |
| Late callback rejected during shutdown | 1 |
| Accepted callback span | 44.831860 s |
| Average callback rate | 60.180417 Hz |
| Unique Target/8-anchor/16-message pipelines | 940 |
| Superseded sequences skipped | 1759 |
| Messages decoded in memory | 15040 |
| Invalid callback / timestamp regression / source-order rejection | 0 |
| Receive interval p50 / p95 / p99 | 16.5 / 21.0 / 24.5 ms |
| Pure pipeline p50 / p95 / p99 | 5.3 / 9.4 / 11.75 ms |
| Callback receipt to decode p50 / p95 / p99 | 14.5 / 22.5 / 26.0 ms |

All accepted inputs passed the existing 24-joint validation, Delta adapter and Canonical construction. Latest processing remained overwrite-only, not backlog replay. Controlled stale clear and final disconnected clear were true. No SDK abort reason was reported (`NONE`).

The underlying pipeline acceptance was **FAIL** because pure-pipeline p99 **11.75 ms exceeded the unchanged 10 ms gate**. No other acceptance failure was listed. This is distinct from the motion window's `INCOMPLETE` status and does not establish an SDK defect. It does not invalidate the historical Phase 2E run, nor prove equivalent performance for the newly instrumented session. Performance cause remains unverified; no runtime redesign or threshold relaxation was made.

## User-approved countdown retry

After the first attempt, the user approved countdown-guided movement/hold/return without intermediate chat replies. One further `right` session used the unchanged supervisor and fixed stdin commands. Japanese guidance used the installed Windows speech synthesizer without changing audio routing or volume. Boundaries were **scheduled**, not user-acknowledged timestamps. The user confirmed afterwards that the motion sequence was completed.

The external chat/tool orchestration still consumed too much time. Marker/state elapsed times were: baseline 9.669693 s; READY_MOVE 12.524453 s; move 26.069337 s; hold 39.857780 s; READY_RETURN 40.807652 s; return 50.807901 s. Observation ended at 55.081595 s before a neutral window could be collected. Result: **60 baseline / 20 held / 0 returned**, `INCOMPLETE / OBSERVATION_ENDED`, no cue aggregate. Post-session acknowledgement cannot reconstruct the missing neutral data.

- Parent total: **56.167260 s**, within 60 s; child exit observed, exit code 0, no forced termination.
- SDK constructor/client/open/close attempts and successes: one each; open result 0; first callback 0.228189 s; observation 55.005347 s.
- **3295** received/accepted/24-joint-valid/Delta/Canonical/published values; no invalid input, ordering rejection, or SDK abort.
- **60.150203 Hz** over accepted span 54.762908 s; receive interval p50/p95/p99 **16.5/22.0/26.5 ms**.
- **1129** memory pipelines, **2166** superseded sequences skipped, **18064** messages decoded.
- Pure pipeline p50/p95/p99 **7.4/11.0/20.05 ms**; callback receipt to decode **16.0/24.5/33.5 ms**. The unchanged 10 ms pure-pipeline p99 criterion again failed. Cause is not established by this timing alone.
- Normal close, stale/disconnected clears and empty final latest slot; protected ReboCap alive, VRChat/SteamVR/probe processes absent at postflight.
- No raw persistence, output send, application/settings operation, multi-client or automatic reconnect. This was an explicitly approved changed-method session, not an automatic retry loop.

Two rightward attempts have now occurred. No third rightward trial or other Live connection is made as part of the subsequent offline timing repair. The user was released from holding a posture.

## Coordinate mapping

| Physical input | SDK axis/sign | Confidence |
|---|---|---|
| Right / Left | Not established | UNVERIFIED |
| Forward / Back | Not measured | UNVERIFIED |
| Up / Down | Not measured | UNVERIFIED |
| Yaw Left / Right | Not measured | UNVERIFIED |

Neither attempt has a complete baseline/held/returned window set. The second has 20 held samples, but no computed cue aggregate or return validation. Movement signs cannot be reconstructed from background callback counts or post-session acknowledgement. Opposite directions are not inferred from an unverified axis.

## Legs, upper body and shoulder finding

Left/Right Knee, Hip, Ankle/Foot, Collar, Shoulder, Elbow and Wrist/Hand controlled comparisons are **not acquired**. Shoulder information-path classification is **E: insufficient data**. No sensor ownership, independence or inherited-endpoint conclusion is drawn from these sessions.

## Adapter and Target validation

The live stream passed value-path validation and produced 940 memory-only Target/anchor/message snapshots. However, known-action SDK-delta-to-Canonical meaning preservation and Target left/right/axis preservation remain **UNVERIFIED** because no motion comparison window completed. Offline synthetic tests are separate evidence, not a substitute for physical observation.

## Implementation and verification

The research harness reuses the existing SDK lifecycle and parent watchdog. An opt-in coherent delta/Canonical handoff feeds a post-pipeline observer. Fixed commands use bounded IPC; exact 60/20/20 RAM windows exclude samples received before each marker. No product scheduler, sender, GUI or alternate SDK lifecycle was added.

The analyzer uses relative Quaternion/axis-angle, global/local joint comparisons, original-delta composition checks, baseline-derived thresholds, neutral-return checks, six endpoint pair comparisons and eight anchor aggregates. Strict fixed-schema sanitizers reject arbitrary strings, extra raw fields and non-finite values.

Independent review found an opposite-side false-FAIL case below that joint's own noise threshold. The minimal fix added its own detection, hold-stability and neutral-return gates, with a regression test. Scope and privacy/provenance reviews accepted the scoped implementation.

Final relevant regression run: **58/58 PASS on Python 3.10, 77.264 seconds**. This is the changed-area run, not a claim that the complete newly expanded suite or every supported Python version was rerun. The historical complete Phase 2E suite was 140 passing tests across Python 3.10/3.11/3.13.

Synthetic PTY testing demonstrated all five controls, complete 60/20/20 windows and clean exit in 46.130585 seconds. An earlier synthetic trial ended on stale input during concurrent test load; no vendor SDK was involved. Legacy synthetic watchdog fixtures were given 8-second rather than 3.5-second test headroom and deterministic burst generation. Live timeouts/performance thresholds were not relaxed.

## Safety and Git

- Raw Pose/time-series files saved: **0**. Short raw windows existed only in bounded process RAM and were cleared/discarded on termination.
- ReboCap setting/Calibration changes by Codex: **0**.
- OSC/UDP/output sends: **0**; official SDK input connection only.
- VRChat/SteamVR launches or operations: **0**.
- Virtual Desktop operations: **0**, intentionally untouched.
- Total Phase 2F-A Live sessions: **2**, both explicitly authorized; automatic reconnects: **0**. No further connection during the offline timing repair.
- No deployment or public release.
- Start and current committed HEAD: `edf603dd2c737800bcb45af9444bf39b3d5a0c4f`.
- Phase 2F changes remain uncommitted and unpushed while the execution method and failed performance gate remain unresolved. See `git status` for the exact current worktree; no history rewrite occurred.

## Next

Do not repeat the chat/tool-paced procedure. The approved countdown method needs local, state-aware guidance without model/tool round trips in its timing-critical path; verify that minimal helper offline, reusing the existing supervisor and all original time limits. Scheduled boundaries and after-session physical confirmation remain distinct. Do not invent timestamps, relax the 10 ms performance criterion, or request a third rightward trial without new permission. Diagnose the performance miss separately without SDK contact. Remaining known motions and any VR output phase remain unexecuted.

## Corrective gate after repeated orchestration error

The user explicitly objected to repeating the same mistake. The mistake was retaining model/tool round trips in a 60-second body-motion procedure after the first timing failure. Replacing text with speech did not remove that dependency. A successful manual synthetic terminal run was insufficient evidence of the actual user-guidance path.

No further body cue or Live connection is part of this correction. Acceptance requires the **same local guidance wrapper and existing supervisor**, using injected synthetic SDK/speech only, to demonstrate complete 60/20/20 acquisition, normal close/exit, and a bounded end-to-end duration. Delayed, failed and hanging speech/control cases must stop without a false PASS or surviving owned child. The parent watchdog and 20/45/55/60-second bounds must not be relaxed. No installed speaker audibility or physical motion is inferred from silent synthetic tests.
