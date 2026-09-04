# Project Charter

## Long-term goal

ReboRetarget will take human motion captured by ReboCap and reconstruct it in real time on a VRChat avatar with different body proportions, producing natural full-body tracking for the user's primary Meta Quest 3, Virtual Desktop, SteamVR, VRChat, and ReboCap environment.

This is real-time **morphology retargeting**: preserve the meaning of human joint motion while solving it on a target skeleton with different segment lengths and widths.

## Problem being solved

Representative failures of direct tracker mapping include:

- An avatar's legs are longer than the user's, so VRChat shows bent knees while the user's real knees are straight.
- A pose may align with outstretched arms but fail during folded-arm or cross-body motion because shoulder width, upper-arm length, and forearm length differ.

A uniform coordinate multiplier cannot independently address thigh/calf balance, hip width, shoulder width, and arm-segment proportions. The intended solution therefore uses the captured skeleton and relevant joint motion to reconstruct target joint positions and orientations.

## Intended result

The long-term user experience is:

1. The user starts ReboCap.
2. ReboRetarget starts automatically, connects to ReboCap, and appears like an added ReboCap capability, without requiring repetitive manual startup and configuration.
3. Native mode continues to use ReboCap's normal SteamVR body trackers.
4. Retarget mode suppresses only the conflicting native body-tracker output, generates retargeted body motion, and sends the planned eight VRChat OSC trackers.
5. Turning retarget mode off or closing ReboCap stops ReboRetarget output, saves the selected profile, restores only settings ReboRetarget changed to their exact prior values, and exits safely.

ReboCap itself need not be modified if an official SDK plus an external attached window or another supported integration can provide this experience.

## Initial functional boundary

The initial product direction includes:

- ReboCap skeleton input and morphology-aware retargeting.
- Planned eight-point VRChat OSC tracker output: Hip, Chest, left/right Knee, left/right Foot, and left/right Upper Arm.
- Knee and shoulder data retained as solver inputs.
- Simple manual avatar morphology parameters and per-avatar profiles.
- Manual profile selection.
- Quest 3 controllers continuing to provide hands through the normal SteamVR-to-VRChat path.
- Safe Native/Retarget switching with exact restoration of prior ReboCap output state.

The initial boundary excludes automatic avatar skeleton analysis, virtual controllers, mesh-surface/collision correction for hands intersecting unusually shaped chests, and a custom SteamVR driver.

Whether automatic startup and window attachment are required for the first technical MVP or for a subsequent usable v1 remains to be confirmed before implementation. They remain part of the long-term product experience.

## Success qualities

- Natural preservation of meaningful knee, leg, shoulder, and upper-arm motion across different body proportions.
- Low latency and low jitter at an expected ReboCap input rate of roughly 60 Hz.
- No backlog playback: if processing falls behind, prefer the newest pose rather than replaying stale poses.
- No unnecessary double smoothing.
- Simple user controls even if the internal solver is sophisticated.
- Exact preservation of unrelated user-tuned ReboCap settings.
- Honest public documentation that distinguishes plans, prototypes, verified behavior, and missing features.

## Future research that must not block the core

Quest 3 IOBT chest yaw may be studied as a low-frequency external reference for ReboCap chest-yaw drift. It is not the primary tracker source and must not delay the main MVP. See `QUEST_CHEST_YAW_ANCHOR.md`.
