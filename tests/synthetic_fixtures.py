"""Synthetic skeletons and poses; no recorded or live motion is used."""

from __future__ import annotations

import math
from typing import Mapping, Sequence, Tuple

from reboretarget import (
    JointDefinition,
    Quaternion,
    REBOCAP_24_PARENT_NAMES,
    SkeletonDefinition,
    SourcePose,
    quaternion_from_axis_angle,
    quaternion_multiply,
    validate_rebocap24_skeleton,
)


def synthetic_human_skeleton(
    *,
    upper_leg: float = 0.43,
    lower_leg: float = 0.43,
    hip_width: float = 0.20,
    shoulder_width_scale: float = 1.0,
) -> SkeletonDefinition:
    """Return a simple T-pose skeleton in confirmed ReboCap joint order."""

    identity = Quaternion.identity()
    half_hip = hip_width * 0.5
    shoulder_scale = float(shoulder_width_scale)
    if not math.isfinite(shoulder_scale) or shoulder_scale <= 0.0:
        raise ValueError("shoulder_width_scale must be finite and positive")
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
            JointDefinition(
                "L_Collar", "Spine3", (-0.08 * shoulder_scale, 0.08, 0.0), identity
            ),
            JointDefinition(
                "R_Collar", "Spine3", (0.08 * shoulder_scale, 0.08, 0.0), identity
            ),
            JointDefinition("Head", "Neck", (0.0, 0.16, 0.0), identity),
            JointDefinition(
                "L_Shoulder",
                "L_Collar",
                (-0.12 * shoulder_scale, 0.0, 0.0),
                identity,
            ),
            JointDefinition(
                "R_Shoulder",
                "R_Collar",
                (0.12 * shoulder_scale, 0.0, 0.0),
                identity,
            ),
            JointDefinition("L_Elbow", "L_Shoulder", (-0.28, 0.0, 0.0), identity),
            JointDefinition("R_Elbow", "R_Shoulder", (0.28, 0.0, 0.0), identity),
            JointDefinition("L_Wrist", "L_Elbow", (-0.25, 0.0, 0.0), identity),
            JointDefinition("R_Wrist", "R_Elbow", (0.25, 0.0, 0.0), identity),
            JointDefinition("L_Hand", "L_Wrist", (-0.10, 0.0, 0.0), identity),
            JointDefinition("R_Hand", "R_Wrist", (0.10, 0.0, 0.0), identity),
        )
    )
    validate_rebocap24_skeleton(skeleton)
    if tuple(joint.parent for joint in skeleton.joints) != REBOCAP_24_PARENT_NAMES:
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


LEG_BEND_FRAME_DEGREES: Tuple[Tuple[float, float], ...] = (
    (0.0, 0.0),
    (5.0, 10.0),
    (10.0, 20.0),
    (15.0, 30.0),
    (20.0, 40.0),
    (25.0, 50.0),
    (30.0, 60.0),
)


def synthetic_leg_bend_sequence(
    skeleton: SkeletonDefinition,
) -> Tuple[SourcePose, ...]:
    """Seven hand-authored frames from straight legs to a symmetric bend."""

    return tuple(
        pose_from_local_rotations(
            skeleton,
            {
                "L_Hip": quaternion_from_axis_angle((1.0, 0.0, 0.0), hip_degrees),
                "R_Hip": quaternion_from_axis_angle((1.0, 0.0, 0.0), hip_degrees),
                "L_Knee": quaternion_from_axis_angle((1.0, 0.0, 0.0), knee_degrees),
                "R_Knee": quaternion_from_axis_angle((1.0, 0.0, 0.0), knee_degrees),
            },
        )
        for hip_degrees, knee_degrees in LEG_BEND_FRAME_DEGREES
    )


ROOT_TRANSLATION_FRAMES: Tuple[Tuple[float, float, float], ...] = (
    (0.0, 1.0, 0.0),
    (0.20, 1.0, 0.0),
    (0.20, 1.15, 0.0),
    (0.20, 1.15, -0.30),
)


def synthetic_root_translation_sequence(
    skeleton: SkeletonDefinition,
) -> Tuple[SourcePose, ...]:
    """Four frames isolating lateral, vertical, and forward/back root motion."""

    return tuple(
        pose_from_local_rotations(skeleton, root_translation=translation)
        for translation in ROOT_TRANSLATION_FRAMES
    )


UPPER_BODY_FRAME_DEGREES: Tuple[Tuple[float, float, float, float], ...] = (
    (0.0, 0.0, 0.0, 0.0),
    (5.0, 2.5, 7.5, 10.0),
    (10.0, 5.0, 15.0, 20.0),
    (15.0, 7.5, 22.5, 30.0),
    (20.0, 10.0, 30.0, 40.0),
)


def synthetic_upper_body_sequence(
    skeleton: SkeletonDefinition,
) -> Tuple[SourcePose, ...]:
    """Five frames exercising Spine3, Collar, Shoulder, and Elbow."""

    return tuple(
        pose_from_local_rotations(
            skeleton,
            {
                "Spine3": quaternion_from_axis_angle((0.0, 1.0, 0.0), spine),
                "L_Collar": quaternion_from_axis_angle((0.0, 0.0, 1.0), collar),
                "L_Shoulder": quaternion_from_axis_angle((0.0, 1.0, 0.0), shoulder),
                "L_Elbow": quaternion_from_axis_angle((0.0, 0.0, 1.0), elbow),
            },
        )
        for spine, collar, shoulder, elbow in UPPER_BODY_FRAME_DEGREES
    )
