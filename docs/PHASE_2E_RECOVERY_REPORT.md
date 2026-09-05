# Phase 2E recovery investigation

Date: 2026-09-05. Starting HEAD: `b88d00121c798c1f5aa272714b6a230dfa0bf66b`.

## Authority and objective

`AUTONOMOUS_ENGINEERING_AUTHORITY.md` supersedes the previous exhausted one-run permission. The present cycle permits at most three sequential bounded attempts after offline recovery tests and review, only at the revised Safe Point and only with a changed implementation or new hypothesis. Virtual Desktop is intentionally preserved; ReboCap settings/calibration, VR application operations, output transmission, and Phase 2F-A are outside this task.

The immediate objective is to correct false receive-time rejection and recover useful evidence even if the native SDK hangs. A synthetic PASS proves the harness, not the Live value path. The prior missing aggregate did not establish successful open or zero callbacks.

## Ranked hypotheses before recovery

Priority is falsification value, not a measured probability.

| Priority | Hypothesis | Evidence / confidence | Smallest test |
|---|---|---|---|
| 1 | Coarse receive clock falsely rejects equal timestamps | Confirmed separate defect; not a hang explanation | Inject coarse versus high-resolution clocks; 60/120 Hz, burst and stalled-consumer regressions offline |
| 2 | Native import, construction, or open blocks | Plausible; no previous checkpoint established its return | Fake stage hangs and parent deadline, then stage checkpoints in one gated Live attempt |
| 3 | Native close/release blocks report delivery | Plausible; synchronous cleanup precedes old final result | Pre-close aggregate, fake close hang, result-before-child-exit distinction |
| 4 | Callback stalls while close waits for serialization lock | Possible, no demonstrated Python lock inversion | Review lock order and real-thread synthetic producer/consumer exits |
| 5 | Final stdout remains buffered during interpreter shutdown | Possible; old final print lacked flush | Flushed fallback output, dedicated aggregate IPC independent of vendor stdout |
| 6 | No calibrated Pose broadcast despite listener/open | Possible for first zero-callback run, not established for missing-result retry | Verified listener plus aggregate callback counts; no calibration/UI operation |

## Known-good comparison and primary sources

The successful Inspector and recovery probe retain the same documented SDK constructor, UnityCoordinate/global option, pose then abnormal-close registration, compatible five-argument callback, explicit port, one client, and Event-based waiting. Clock and result-observability differences are corrected without changing the SDK or introducing reconnect/polling.

- [Official SDK](https://doc.rebocap.com/en_US/SDK/) specifies 24 joints at 60 fps after Action Calibration, Python SDK v2 support for Python 3.6–3.12, and no published lifecycle timeout guarantee. The v2 `get_last_msg` deadlock note does not diagnose these callback-only clients, which do not call that API.
- [Broadcast configuration](https://doc.rebocap.com/en_US/ui_help_doc/control/config.html) describes the default port and occupied-port increment. Listener presence is not proof of Pose generation.
- [Python time](https://docs.python.org/3.10/library/time.html#time.perf_counter) describes the high-resolution monotonic clock used consistently for receive, age, deadlines, and latency.
- [Python stdout](https://docs.python.org/3.10/library/sys.html#sys.stdout) documents noninteractive buffering, motivating evidence recovery independent of final stdout.
- [Python multiprocessing](https://docs.python.org/3.10/library/multiprocessing.html) documents Windows spawn, termination bypassing child cleanup, and IPC/lock risks. Forced child termination is never reported as graceful SDK close.

## Changes and offline evidence

- Both probe clock defaults now use `perf_counter`; source ordering and strict receive watermarks remain unchanged. First-callback delay and last-callback age share the same clock domain.
- Optional aggregate-only checkpoints cover construction, registration, open, observation heartbeat, pre-close, close and completion. The pre-close snapshot does not claim a successful close or PASS. The standalone fallback final print is flushed.
- `research/supervised_retarget_probe.py` imports the SDK only in its spawned child, suppresses vendor Python/native stdout/stderr, and receives bounded JSON bytes on a separate pipe. A daemon reader prevents partial IPC from blocking the parent. Only the latest aggregate/checkpoint is retained.
- The parent uses a separate total deadline with cleanup reserve, terminates only its own child, observes exit, and cannot PASS on termination, supervision/IPC error, missing/malformed final evidence or deadline violation. A final aggregate does not prove that child/native shutdown completed.
- Eight probe regressions and fourteen supervisor tests bring the suite from 118 to **140 passing tests** on Python 3.10, 3.11 and 3.13 (19.660 / 19.581 / 19.697 seconds). Tests cover synthetic 60/120 Hz, bursts and consumer stall; real spawned import/construction/open/close/exit hangs; no callback versus no aggregate; malformed input/final packets; interruption cleanup; partial IPC; and captured Python/native output suppression. No vendor SDK is used by tests.
- Four subagents covered probe clock/lifecycle implementation, parent supervisor/fake hangs, SDK/Inspector evidence plus publication review, and independent Scope Guard. Scope Guard found no unnecessary implementation; publication/privacy review accepted the original source/synthetic fixtures and aggregate-only boundary. A separate safety peer review accepted the supervisor before Live and independently confirmed the resulting Phase 2E PASS.

## Live investigation cycle

Attempts used: **1 / 3**. Cycle complete with **Phase 2E PASS**. Attempts 2 and 3 were not needed or executed. No reconnect occurred.

Attempt 1 change/hypothesis: applied the proven clock correction and process isolation together, preserving known-good SDK constructor/options/registration. Tested whether the previously unlocated stall recurred and made the last returned stage observable. Observation was 20 seconds; parent total deadline was 45 seconds, reserving one second for child termination/exit verification. Thresholds, SDK options, calibration and broadcast settings were not changed to obtain a PASS.

Read-only preflight, an in-run snapshot, and postflight confirmed the protected original ReboCap process remained alive, VRChat/SteamVR were absent, and Virtual Desktop Service/Streamer retained the same processes. The ReboCap listener was present before/after; its pre-existing peer was its own GUI child, not a competing external test client. The owned probe was absent after exit. Visible calibration/skeleton state was not inferred from a listener or inspected via UI; actual callback delivery established stream availability in this run.

| Attempt evidence | Result |
|---|---|
| Parent start / hard deadline | Relative T=0 / T=45.000 seconds; Python 3.10 |
| Parent end / total elapsed | T=20.249216 seconds, within deadline |
| SDK observation duration | 20.016129 seconds |
| Checkpoints / final checkpoint | 33 validated packets; `result_ready` at child elapsed 20.039918 seconds |
| Final result recovered / child exit | Yes / exit code 0, exit observed |
| Termination requested / IPC errors | No / 0 |
| SDK constructor / open / close | One each; open code 0; open and close successful |
| First callback after open attempt | 0.205819 seconds |
| Callbacks / accepted / rejected | 1200 / 1200 / 0 |
| Delta / Canonical / latest publish | 1200 / 1200 / 1200 |
| 24-joint/root/Quaternion/timestamp invalidity | 0; source and receive order rejections 0 |
| Accepted receive-span rate | 60.557342 Hz over 19.799416 seconds |
| Latest-only consumption | 429 unique sequences; 771 skipped superseded sequences; 1199 total slot replacements |
| Eight-anchor sets / sixteen-message sets / decoded messages | 429 / 429 / 6864, all memory-only |
| Controlled STALE / final DISCONNECTED clearing | Both true; no retained latest sample |
| Natural external disconnect | Not triggered; remains unverified, not required for this gate |
| Final acceptance failed / insufficient | Empty / empty |

The consumer setting is a ceiling of 30 Hz, not a demonstrated 30 Hz scheduler: 429 processed samples over this observation is approximately 21.4 Hz. The gate validates latest-only handoff and value processing, not product scheduling, anatomical accuracy, avatar quality, or physical end-to-end tracking latency.

### Measured timings

All values are milliseconds. Percentiles are bounded-histogram approximations, not exact quantiles. Counts are included to distinguish callback from consumer measurements; a histogram value of zero does not mean zero CPU time.

| Boundary | Samples | p50 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|
| Receive interval | 1199 | 16.5 | 18.0 | 18.5 | 29.3692 |
| Source interval | 1199 | 16.5 | 18.0 | 18.0 | 19.999981 |
| Input validation | 1200 | 0.05 | 0.15 | 0.7 | 1.0504 |
| Delta-to-Canonical adapter | 1200 | 0.85 | 1.5 | 3.3 | 4.6776 |
| Target FK | 429 | 1.2 | 2.05 | 2.45 | 4.6252 |
| Anchor builder | 429 | 0.1 | 0.2 | 0.25 | 0.3790 |
| OSC representation | 429 | 0.15 | 0.25 | 0.35 | 0.5860 |
| Memory codec | 429 | 0.1 | 0.2 | 0.3 | 0.5894 |
| Pure consumer pipeline | 429 | 1.6 | 2.7 | 3.25 | 5.0704 |
| Callback receipt to memory decode | 429 | 10.0 | 17.5 | 18.5 | 19.4387 |

The pure-pipeline p99 passed the predeclared 10 ms budget. Source interval mean was 16.666389 ms, consistent with roughly 60 Hz. The receive-span rate is not interchangeable with source cadence. There were 13 receive intervals below 4 ms, zero gaps at least 50 ms, and no timestamp regressions. No raw source timestamps, motion values, or time series were saved.

## Root cause and remaining boundaries

- **Confirmed and fixed:** coarse-clock false receive-order rejection. High-resolution monotonic clock regressions and this Live run show no false rejection.
- **Confirmed design weakness and addressed:** the old in-process observation loop did not bound native lifecycle calls and final-only output could lose evidence. Parent-owned isolation/deadline and intermediate aggregates address this; fake hang tests prove the supervisor behavior on this OS/runtime.
- **Unknown historical cause:** which stage blocked in the previous 43.1-second observation and why the initial run delivered zero callbacks. The successful recovery run does not retroactively prove the clock was the hang cause or establish a native SDK defect.
- **Not proven:** independent external SDK multi-client safety; true transport-disconnect recovery; known-action axes; shoulder-present/absent effect; real-avatar tracker offsets/IK quality; product scheduling; SDK redistribution permission. No native release timeout guarantee is assumed.

The watchdog is tested and this run is measured inside its deadline. Windows scheduling/process creation is not a hard-real-time guarantee; no claim is made about an unresponsive OS. Forced termination of synthetic children bypasses SDK cleanup by design; the actual Live child exited normally.

ReboCap configuration/calibration/output changes: 0. Virtual Desktop operations: 0; it was intentionally left running under user permission. VR stack starts/restarts: 0. OSC/UDP/direct output sends: 0. Raw Pose/time-series/message-byte persistence: 0. Official SDK WebSocket receive-client traffic is the only authorized Live communication.

## Next action and publication

Phase 2E PASS ends this investigation cycle; do not consume the remaining two attempts merely because permission exists. Phase 2F-A is **WAITING_FOR_USER / NOT AUTHORIZED TO EXECUTE**. Its existing controlled-motion protocol is the next input-semantics gate, with safe user-selected motions and separate authorization; no OSC output or VRChat startup follows automatically.

The implementation, tests and this sanitized narrative contain no vendor SDK/source/binary, raw motion, private endpoint, installation path or credentials. `f2f3a55` records the durable authority change and `a165e08` records the tested recovery implementation. Final report commit/push/status are reported from actual Git results, not guessed in this document. No product was deployed or released.
