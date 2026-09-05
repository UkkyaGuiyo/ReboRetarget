# Phase 2E retry report

Date: 2026-09-05

**Run: ABORTED. Phase 2E: UNVERIFIED. No further connection authorized.**

## Authorization and observed environment

The user explicitly permitted existing Virtual Desktop Service/Streamer and established TCP connections for this retry. The revised Safe Point required the same running ReboCap process, zero VRChat and SteamVR processes, and no ReboCap setting changes. Read-only preflight satisfied these conditions. Virtual Desktop Service/Streamer were intentionally left running under user permission; they are not a failure reason.

The official local SDK remained outside the repository. The ReboCap-owned listener was the verified documented default port. The one launched probe was configured for Python 3.10, UnityCoordinate, global rotations, at most one SDK client, a 20-second observation, provisional 250 ms stale threshold, raw Quaternion tolerance 1e-4, 30 Hz consumer limit, and the existing synthetic Target/anchor memory-only pipeline. Actual constructor/open completion is unverified. ReboCap executable product metadata remained 0.48.0.0; the previously observed UI build was Release_V02_Beta02.

## Execution evidence

- Exactly one new probe process was launched. No automatic reconnect or subsequent SDK run occurred.
- SDK diagnostic output was filtered transiently; only a line beginning `RESULT_JSON=` would be returned. No output was redirected to a file.
- No aggregate line was returned. The process was still alive at a measured elapsed time of 43.1 seconds, beyond its configured 20-second observation.
- The parent then force-stopped only that newly launched, identity-verified Python probe to prevent an indefinite connection. The exact termination elapsed time was not sampled, so a precise connected duration and independently measured 60-second upper bound are unavailable.
- The terminal ended with exit code 1 after termination. No final SDK open result, close result, callback count, or timing aggregate was recovered.
- Postflight confirmed the same ReboCap process and executable, one maintained listener, and its remaining established connection. VRChat and SteamVR were still absent. Virtual Desktop Service/Streamer retained their original processes.
- ReboCap settings/calibration/native output, Virtual Desktop, Quest, Meta/Oculus, and VR applications were not changed during this retry. No OSC/UDP/direct output sender was invoked. No Raw Pose or motion time series was saved.

**No aggregate is not evidence of zero callbacks.** Callback count, first-arrival delay, input Hz, intervals, joint validity, timestamps, delta/canonical successes, latest-pose handoff, and all pipeline latencies are unavailable for this run. The prior run's zero-callback result must not be copied into this one.

## Offline comparison and bounded cause assessment

The successful historical Inspector and the safety probe use the same SDK constructor, UnityCoordinate, global rotation option, pose-then-abnormal-close registration order, five SDK callback arguments, and one explicit-port open call. Both retain the SDK object while observing and use Event waits that release the Python GIL. The Inspector waits approximately 250 ms; the probe consumes at up to 30 Hz. Additional validation occurs after the probe callback counter is incremented, so invalid Pose checks alone do not explain a zero callback counter.

The public official Python wrapper calls compiled open, close, and object release synchronously. It exposes no Python-side timeout on those calls. The probe checks its deadline only after `sdk.open()` returns and prints its final aggregate only after `sdk.close()` returns. Its wrapper destructor also calls native release; if destruction occurs before the print, release could block it, but native object retention and destruction timing were not established. A blocked lifecycle call can prevent the aggregate and defeat the in-process observation deadline. The observed hang cannot be assigned to any one of these stages from current evidence.

Static review found no demonstrated Python lock inversion in the probe. A native callback/GIL/join interaction remains a hypothesis, not a confirmed cause. No binary, memory, injection, hooking, or additional reverse-engineering work was performed.

A separate concrete timing defect was reproduced offline: on the selected Windows Python 3.10 runtime, `time.monotonic` uses GetTickCount64 at 0.015625-second resolution, whereas the Inspector's receive clock `time.perf_counter` uses QueryPerformanceCounter at 0.0000001-second resolution. The probe strictly rejects equal receive timestamps, so a burst can be falsely rejected by the coarse clock. A synthetic threaded 120-frame burst aborted with `RECEIVE_TIMESTAMP_ORDER` after 52 accepted frames using the default clock; the same fixture using `perf_counter` accepted all 120 with no abort and the producer exited. These are ad-hoc offline evidence, not a Live-hang reproduction or a newly committed regression test. A future fix must use the high-resolution monotonic clock consistently for receive, age, deadline, and latency, without mixing clock domains or weakening source timestamp ordering.

Official documentation says Pose broadcast starts after Action Calibration, at 60 frames per second with 24 joints. The current Action/Pose Calibration and broadcast state were not independently observed. Listener presence does not establish Pose generation. Python SDK v2 documents Python 3.6 through 3.12 compatibility; Python 3.10 matches that range, but compatibility with the exact installed ReboCap build remains unproven by this retry.

## Next permitted work

Before requesting another live run, fix and regression-test the coarse receive clock, then prepare an offline-tested bounded runner with parent-enforced termination timing and sanitized lifecycle checkpoints before/after SDK open, close, and release. Preserve a bounded aggregate before potentially blocking SDK cleanup, and measure first callback arrival relative to open attempt. This diagnostic work does not authorize another SDK connection. Do not change SDK options speculatively or restore the VR stack to reproduce the earlier Inspector environment.

Phase 2F-A remains NO-GO because Phase 2E has not passed and controlled motion needs separate authorization.

## Verification and publication

This retry changed documentation only. Existing 118-test results apply to the prior code revision and do not prove native SDK lifecycle behavior. No committed test was added and the repository test suite was not rerun; the ad-hoc synthetic clock A/B described above was performed offline. Source was not changed. The documentation diff and publication scan are checked before commit; commit/push results are recorded in the final response rather than guessed here. No raw result JSON, SDK files, identifiers, local SDK paths, or vendor diagnostic logs are included.

## Primary sources

- [Official SDK interface and Python SDK compatibility](https://doc.rebocap.com/en_US/SDK/)
- [Official WebSocket broadcast configuration](https://doc.rebocap.com/en_US/ui_help_doc/control/config.html)

The official Python wrapper was inspected read-only from the existing external local copy. Vendor source was not copied into this repository.
