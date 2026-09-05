# Autonomous engineering authority

Accepted user directive: 2026-09-05. Scope: ReboRetarget development, currently Phase 2E recovery. This records the user's authority, not an agent-created expansion of it. Newer explicit user instructions always prevail.

## Work selection and evidence

Do not stop the project merely because one method is blocked or a test is UNVERIFIED. Stop that branch and choose useful safe work. Observe, distinguish missing evidence, rank at least three plausible causes by evidence/confidence/impact/test cost, run the smallest falsification test, fix, add regression coverage, and reevaluate. Prefer offline tests and comparison with the successful `research/live_pose_inspector.py`. Do not invent work, repeat an unchanged live test, or treat a hypothesis as a root cause.

Delegate independent implementation, SDK-lifecycle analysis, tests, scope review, and publication review when useful. Keep the coordinator responsible for integration and safety. Apply the existing Scope Guard review gate to nontrivial code changes.

## Levels of authority

- **A, autonomous offline:** original code, synthetic tests/benchmarks, docs, public primary-source research, Git/provenance review. Preserve the legal/publication boundaries; SDK material and raw motion never enter the repository.
- **B, conditional live:** the existing official local SDK, one receive-only client, aggregate-only evidence, no output send, under the gate below.
- **C, separately authorized:** calibration, protected settings/VR Output, VR application startup, OSC transmission, headset or controlled body motion, Native/Retarget switching, GUI interaction, or expanded reverse engineering. Existing prohibitions on bypass, injection, binary patching, copied proprietary code, and private access remain in force. Computer-use is prohibited by the current user instruction.

## Standing Phase 2E permission

The earlier exhausted one-run permission is superseded for recovery by **at most three bounded Live retries in one investigation cycle**, not three simultaneous clients. Before each attempt record the actual code change or new falsifiable hypothesis since the previous attempt. The cycle limit is not reset by renaming a task or opening a new session. Track usage in the current recovery report.

All of these must hold immediately before connection:

- ReboCap is already user-started, with the protected existing process identity preserved; no restart, configuration, or calibration operation is necessary.
- VRChat and SteamVR have zero processes. Read-only inspection identifies the existing local listener and absence of a competing external SDK test client.
- Virtual Desktop Service/Streamer and established connections are permitted environmental variables, not blockers. Do not stop, kill, reconfigure, or change its service/ACL/UAC/registry state.
- Only the separately obtained official local SDK is loaded, only in the child probe. UnityCoordinate/global rotation remain the known-good options unless evidence justifies a permitted change.
- One receive-only client; no reconnect loop, multi-client experiment, OSC/UDP/direct output send, Raw Pose persistence, or other application operation.
- An offline-tested parent watchdog enforces a total maximum of 60 seconds, including lifecycle hangs, with cleanup allowance. Only its owned child may be terminated. Parent retains sanitized checkpoints/aggregate evidence even when final SDK cleanup stalls.
- The previous attempt has ended, the environment remains stable, and there is a recorded change or new hypothesis. An unexplained application crash stops live work.

Unknown visible skeleton/calibration/broadcast state is recorded honestly, not assumed PASS and not fixed by operating the UI. No body-motion cues are authorized. When the cycle is exhausted or a live prerequisite fails, continue useful offline comparison, test work, documentation, or a vendor inquiry draft; do not connect again merely to obtain more samples.

## Recovery acceptance

First fix the coarse receive clock consistently with a high-resolution monotonic clock, without weakening source timestamp ordering. Independently isolate native SDK import/construction/open/close from the parent, recover intermediate aggregates, and prove timeout behavior with fake SDK import/construction/open/close hangs, no callbacks, bursts, malformed frames, and normal callbacks. Offline tests and independent review precede Live.

Phase 2E PASS requires the actual Live acceptance evidence in `LIVE_REBOCAP_ADAPTER_SAFETY_PROTOCOL.md`; code, synthetic PASS, or socket open alone are insufficient. PASS permits documentation/regression/review work, not Phase 2F-A. Controlled motion remains WAITING_FOR_USER under its separate protocol.

Reports separate confirmed/probable/unknown causes and include each attempt's start, deadline, checkpoint, callback evidence, exit, result recovery, environment preservation, tests, and Git state. Never translate missing aggregates into zero callbacks.
