"""Synthetic skeletons and poses; no recorded or live motion is used."""

from __future__ import annotations

from typing import Mapping, Sequence

from reboretarget import (
    JointDefinition,
    Quaternion,
    SkeletonDefinition,
    SourcePose,
    quaternion_multiply,
    validate_rebocap24_skeleton,
)


# Fixture-only conventional SMPL-style hierarchy.  The 24 name/order contract
# is confirmed; this parent array is provisional and is not a public core API
# or a claimed normative ReboCap SDK contract.
SYNTHETIC_CONVENTIONAL_PARENT_NAMES = (
    None,
    "Pelvis",
    "Pelvis",
    "Pelvis",
    "L_Hip",
    "R_Hip",
    "Spine1",
    "L_Knee",
    "R_Knee",
    "Spine2",
    "L_Ankle",
    "R_Ankle",
    "Spine3",
    "Spine3",
    "Spine3",
    "Neck",
    "L_Collar",
    "R_Collar",
    "L_Shoulder",
    "R_Shoulder",
    "L_Elbow",
    "R_Elbow",
    "L_Wrist",
    "R_Wrist",
)


def synthetic_human_skeleton(
    *,
    upper_leg: float = 0.43,
    lower_leg: float = 0.43,
    hip_width: float = 0.20,
) -> SkeletonDefinition:
    """Return a simple T-pose skeleton in confirmed ReboCap joint order."""

    identity = Quaternion.identity()
    half_hip = hip_width * 0.5
    skeleton = SkeletonDefinition(
        (
            JointDefinition("Pelvis", None, (0.0, 0.0, 0.0), identity),
            JointDefinition("L_Hip", "Pelvis", (-half_hip, 0.0, 0.0), identity),
            JointDefinition("R_Hip", "Pelvis", (half_hip, 0.0, 0.0), identity),
            JointDefinition("Spine1", "Pelvis", (0.0, 0.15, 0.0), identity),
            JointDefinition("L_Knee", "L_Hip", (0.0, -upper_leg, 0.0), identity),
            JointDefinition("R_Knee", "R_Hip", (0.0, -upper_leg, 0.0), identity),
            JointDefinition("Spine2", "Spine1", (0.0, 0.15, 0.0), identity),
            JointDefinition("L_Ankle", "L_Knee", (0.0, -lower_leg, 0.0), identity),
            JointDefinition("R_Ankle", "R_Knee", (0.0, -lower_leg, 0.0), identity),
            JointDefinition("Spine3", "Spine2", (0.0, 0.15, 0.0), identity),
            JointDefinition("L_Foot", "L_Ankle", (0.0, 0.0, 0.18), identity),
            JointDefinition("R_Foot", "R_Ankle", (0.0, 0.0, 0.18), identity),
            JointDefinition("Neck", "Spine3", (0.0, 0.12, 0.0), identity),
            JointDefinition("L_Collar", "Spine3", (-0.08, 0.08, 0.0), identity),
            JointDefinition("R_Collar", "Spine3", (0.08, 0.08, 0.0), identity),
            JointDefinition("Head", "Neck", (0.0, 0.16, 0.0), identity),
            JointDefinition("L_Shoulder", "L_Collar", (-0.12, 0.0, 0.0), identity),
            JointDefinition("R_Shoulder", "R_Collar", (0.12, 0.0, 0.0), identity),
            JointDefinition("L_Elbow", "L_Shoulder", (-0.28, 0.0, 0.0), identity),
            JointDefinition("R_Elbow", "R_Shoulder", (0.28, 0.0, 0.0), identity),
            JointDefinition("L_Wrist", "L_Elbow", (-0.25, 0.0, 0.0), identity),
            JointDefinition("R_Wrist", "R_Elbow", (0.25, 0.0, 0.0), identity),
            JointDefinition("L_Hand", "L_Wrist", (-0.10, 0.0, 0.0), identity),
            JointDefinition("R_Hand", "R_Wrist", (0.10, 0.0, 0.0), identity),
        )
    )
    validate_rebocap24_skeleton(skeleton)
    if tuple(joint.parent for joint in skeleton.joints) != SYNTHETIC_CONVENTIONAL_PARENT_NAMES:
        raise AssertionError("synthetic fixture hierarchy does not match its definition")
    return skeleton


def pose_from_local_rotations(
    skeleton: SkeletonDefinition,
    local_overrides: Mapping[str, Quaternion] | None = None,
    *,
    root_translation: Sequence[float] = (0.0, 1.0, 0.0),
) -> SourcePose:
    """Construct internally consistent globals from hand-authored locals."""

    overrides = local_overrides or {}
    indices = {joint.name: index for index, joint in enumerate(skeleton.joints)}
    globals_out = []
    for joint in skeleton.joints:
        local = overrides.get(joint.name, joint.rest_local_rotation)
        if joint.parent is None:
            globals_out.append(local)
        else:
            globals_out.append(
                quaternion_multiply(globals_out[indices[joint.parent]], local)
            )
    return SourcePose(tuple(root_translation), tuple(globals_out))
