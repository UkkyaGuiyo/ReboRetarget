"""Pure adapter from ReboCap SDK T-pose deltas to canonical source poses.

This module contains no SDK client, network, process, filesystem, or clock
access.  It only adapts already-constructed immutable values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from .fk import (
    Quaternion,
    QuaternionLike,
    SkeletonDefinition,
    SourcePose,
    Vector3,
    forward_kinematics,
    quaternion_multiply,
    validate_rebocap24_skeleton,
)


@dataclass(frozen=True, slots=True)
class ReboCapDeltaPose:
    """SDK-shaped Pelvis translation and 24 global T-pose rotation deltas."""

    root_translation: Vector3
    sdk_global_rotation_deltas: Tuple[Quaternion, ...]

    def __post_init__(self) -> None:
        validated = SourcePose.from_rebocap24(
            self.root_translation, self.sdk_global_rotation_deltas
        )
        object.__setattr__(self, "root_translation", validated.root_translation)
        object.__setattr__(
            self,
            "sdk_global_rotation_deltas",
            validated.global_rotations,
        )

    @classmethod
    def from_rebocap24(
        cls,
        root_translation: Sequence[float],
        sdk_global_rotation_deltas_wxyz: Sequence[QuaternionLike],
    ) -> "ReboCapDeltaPose":
        """Validate the confirmed 24-joint order/shape and normalize values."""

        validated = SourcePose.from_rebocap24(
            root_translation,
            sdk_global_rotation_deltas_wxyz,
        )
        return cls(validated.root_translation, validated.global_rotations)


def source_bind_global_rotations(
    source_bind_skeleton: SkeletonDefinition,
) -> Tuple[Quaternion, ...]:
    """Compose source bind-local rotations into bind-global rotations."""

    validate_rebocap24_skeleton(source_bind_skeleton)
    source_bind_local_rotations = tuple(
        joint.rest_local_rotation for joint in source_bind_skeleton.joints
    )
    source_bind_world_transforms = forward_kinematics(
        source_bind_skeleton,
        (0.0, 0.0, 0.0),
        source_bind_local_rotations,
    )
    return tuple(transform.rotation for transform in source_bind_world_transforms)


def adapt_rebocap_delta_pose(
    delta_pose: ReboCapDeltaPose,
    source_bind_skeleton: SkeletonDefinition,
) -> SourcePose:
    """Return canonical absolute globals using ``sdk_delta * bind_global``.

    The multiplication order follows the official Unity SDK v4 and Unreal
    Engine plugin v2 integrations.  It is intentionally kept outside the
    source-agnostic FK core.
    """

    validate_rebocap24_skeleton(source_bind_skeleton)
    if len(delta_pose.sdk_global_rotation_deltas) != len(
        source_bind_skeleton.joints
    ):
        raise ValueError("ReboCap delta pose must contain exactly 24 rotations")

    source_bind_globals = source_bind_global_rotations(source_bind_skeleton)
    canonical_source_global_rotations = tuple(
        quaternion_multiply(sdk_rotation_delta, source_bind_global_rotation)
        for sdk_rotation_delta, source_bind_global_rotation in zip(
            delta_pose.sdk_global_rotation_deltas, source_bind_globals
        )
    )
    return SourcePose(
        delta_pose.root_translation,
        canonical_source_global_rotations,
    )
