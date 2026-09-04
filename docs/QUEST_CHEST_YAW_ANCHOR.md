# Quest 3 Chest Yaw Anchor — Future Research

## Position in the project

This is an independent, optional research track. It must not block or redefine the core ReboRetarget MVP.

ReboCap remains the normal full-body tracking source. Quest 3 IOBT chest yaw is considered only as a low-frequency external reference for observing, and possibly later correcting, long-duration ReboCap chest-yaw drift.

## Proposed relationship

```text
ReboCap skeleton     -> normal full-body retargeting
Quest IOBT chest yaw -> slow external reference only
```

Quest data must not replace fast ReboCap motion or drive per-frame corrections.

## Candidate modes

- **OFF** — no Quest yaw monitoring or effect.
- **MONITOR** — compare signals and record metrics; never modify output.
- **AUTO** — apply guarded correction only after MONITOR evidence proves it safe and useful.

MONITOR is the required first research mode. AUTO is not approved for implementation merely because it is described here.

## Safety and signal rules

- If Quest data is unavailable, stale, discontinuous, or unstable, do nothing.
- Never correct from one frame.
- Separate a stable coordinate-frame offset from time-varying drift.
- Apply any future correction gradually, with bounded rate/magnitude and clear confidence gates; do not snap.
- Preserve high-frequency ReboCap motion.
- Treat Chest Yaw Bias as session-only state, not an avatar profile parameter.
- Observation must be time-aligned before interpreting a difference as drift.

## Questions MONITOR research must answer

- Can Quest IOBT chest yaw be accessed through a supported, lawful interface in the target setup?
- What are its coordinate frame, update rate, latency, confidence/validity signals, and discontinuity behavior?
- How much of the observed difference is fixed offset versus true time drift?
- When does Quest yaw become less reliable than ReboCap yaw?
- What time window and thresholds distinguish drift from normal torso motion?
- Can monitoring run without disrupting the standard Quest/Virtual Desktop/SteamVR/VRChat path?

## Evidence required before considering AUTO

- Repeatable sessions showing a meaningful, slowly varying ReboCap yaw error against a sufficiently stable reference.
- False-positive and dropout characterization across representative movements.
- A replay or monitor-only evaluation showing that proposed correction would improve drift without damaging intentional motion.
- Defined disable/fallback behavior and bounded gradual correction.
- Explicit user approval to move this track from monitoring research into output-changing implementation.
