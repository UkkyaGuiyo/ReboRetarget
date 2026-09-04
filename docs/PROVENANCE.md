# Provenance and History Audit

## Audit scope and snapshot

Snapshot date: 2026-09-05

- Baseline commit: `f1c352684553289f76fe0a97d5e80ba5b0174333`.
- At that baseline, local `main` matched `origin/main` and the working tree was clean.
- The baseline contained 12 reachable commits and 34 files tracked at `HEAD`.
- The audit covered tracked files at `HEAD`, all objects reachable from local branches/tags, and a separate local-unreachable-object check.

Here, **tracked** means the files recorded by the baseline commit. **Reachable** means an object referenced through the audited local branch/tag graph and therefore potentially publishable with those refs. **Unreachable** means a clone-local Git object outside that graph; it is reported separately and is not described as public history.

## Component provenance

| Component | Provenance |
|---|---|
| `reboretarget/fk.py` | Independently authored standard-library Quaternion, rotation-delta, and FK mathematics. It uses general mathematical formulas and requires no SDK code. |
| `reboretarget/rebocap_adapter.py` | Independently authored adapter for the documented T-pose-delta composition and confirmed joint contract. Official behavior informed the interface; vendor source was not copied. |
| `reboretarget/tracker_anchors.py` | Project-specific semantic-anchor implementation with synthetic replaceable fixtures. |
| `reboretarget/vrchat_osc.py` | Independently authored minimal representation/OSC codec based on public VRChat, Unity, and OSC specifications; it has no OSC library or sender dependency. |
| `reboretarget/latest_pose.py` | Independently authored standard-library capacity-one synchronization/state primitive. |
| `tests/` | Hand-authored synthetic fixtures and deterministic tests; no captured motion, vendor fixture, or SDK code. |
| `research/live_pose_inspector.py` | Project-authored aggregate observer. It dynamically imports a user-supplied official SDK outside the repository and retains aggregates rather than raw Pose frames. |
| `docs/` | Project-authored summaries, decisions, test reports, factual identifiers, citations, and sanitized aggregates; no vendor archive, decompiled source, or raw log. |

The factual 24-joint name list and public interface/address constants naturally may match official documentation. They are factual interface data and are not treated as copied implementation.

## Authoritative technical inputs

- ReboCap SDK interface: <https://doc.rebocap.com/en_US/SDK/>
- ReboCap Unity SDK v4 archive evidence, SHA-256: `E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF`
- ReboCap Unreal Engine plugin v2 archive evidence, SHA-256: `AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53`
- VRChat OSC trackers: <https://docs.vrchat.com/docs/osc-trackers>
- OSC 1.0 specification: <https://opensoundcontrol.stanford.edu/spec-1_0.html>
- Unity rotations: <https://docs.unity3d.com/6000.0/Documentation/Manual/QuaternionAndEulerRotationsInUnity.html>
- OpenVR driver documentation: <https://github.com/ValveSoftware/openvr/blob/master/docs/Driver_API_Documentation.md>

The official archives were inspected outside this repository and were not committed. References and hashes establish evidence provenance, not redistribution rights.

## Reachable-history scan

At the baseline snapshot:

- 12 commits were reachable.
- 34 files were tracked at `HEAD`.
- 88 unique blobs were reachable, totaling 946,212 bytes.
- No historical filename indicated an archive or binary-like artifact.
- No reachable blob contained NUL data or recognized binary magic.
- The scan detected no private-key/token pattern, local absolute user path, raw motion/log artifact, device identifier, or account identifier in reachable blob content.

The repository URL and ordinary Git author metadata are expected public repository metadata. The content result above is not a claim that no identity metadata exists anywhere on GitHub.

## Local unreachable-object note

A separate local `git fsck --unreachable --no-reflogs` snapshot found one superseded unreachable commit and 13 unreachable blobs. Three superseded Phase 0 draft blobs each contained one local absolute path. The path text is intentionally not reproduced here.

None of those objects was reachable from `main` or another pushed ref; an ordinary push does not transfer unreachable objects. No object cleanup or history rewrite was performed. Unreachable-object counts are clone-local and may change through normal Git garbage collection. This note is transparency about the audited clone, not a report of public-history exposure.

## Audit limitations

- Pattern and exact-match scans are heuristic; they cannot prove universal absence of encoded secrets or every possible copyright similarity.
- The available official SDK/example set was compared for material exact copying; no material code-block match was identified beyond factual interface/joint data.
- The audit covers this clone/ref snapshot, not GitHub issues, caches, forks, release assets, Actions artifacts, or future commits.
- Provenance review does not determine vendor-license meaning or commercial rights.
- Every future dependency or copied asset requires a new source/license review.

## Future-change gate

Before a public push, inspect staged names/content, the diff, reachable history, binary/archive additions, secrets/paths/identifiers, and dependency changes. Any serious finding invokes the STOP and no-automatic-history-rewrite rule in [`LEGAL_BOUNDARIES.md`](LEGAL_BOUNDARIES.md). Update this provenance snapshot only when a component, source, dependency, or history fact materially changes.
