"""Pure semantic tracker-anchor transforms derived from a TargetPose."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Sequence, Tuple

from .fk import (
    Quaternion,
    QuaternionLike,
    SkeletonDefinition,
    TargetPose,
    Vector3,
    quaternion_multiply,
    rotate_vector,
    validate_rebocap24_skeleton,
)


class SemanticTrackerRole(str, Enum):
    HIP = "Hip"
    CHEST = "Chest"
    LEFT_KNEE = "Left Knee"
    RIGHT_KNEE = "Right Knee"
    LEFT_FOOT = "Left Foot"
    RIGHT_FOOT = "Right Foot"
    LEFT_UPPER_ARM = "Left Upper Arm"
    RIGHT_UPPER_ARM = "Right Upper Arm"


SEMANTIC_TRACKER_ROLES: Tuple[SemanticTrackerRole, ...] = tuple(
    SemanticTrackerRole
)


def _vector3(value: Sequence[float], label: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{label} must contain exactly 3 values")
    converted = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in converted):
        raise ValueError(f"{label} must be finite")
    return (converted[0], converted[1], converted[2])


def _quaternion(value: QuaternionLike, label: str) -> Quaternion:
    try:
        components = (
            (value.w, value.x, value.y, value.z)
            if isinstance(value, Quaternion)
            else tuple(value)
        )
        normalized = Quaternion(*components).normalized()
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{label} must be a finite non-zero (w,x,y,z) quaternion"
        ) from error
    return normalized


@dataclass(frozen=True, slots=True)
class TrackerAnchorDefinition:
    role: SemanticTrackerRole
    parent_joint: str
    local_position_offset: Vector3
    local_rotation_offset: Quaternion = field(default_factory=Quaternion.identity)

    def __post_init__(self) -> None:
        if not isinstance(self.role, SemanticTrackerRole):
            raise ValueError("role must be a SemanticTrackerRole")
        if not isinstance(self.parent_joint, str) or not self.parent_joint:
            raise ValueError("parent_joint must be a non-empty string")
        object.__setattr__(
            self,
            "local_position_offset",
            _vector3(self.local_position_offset, "local_position_offset"),
        )
        object.__setattr__(
            self,
            "local_rotation_offset",
            _quaternion(self.local_rotation_offset, "local_rotation_offset"),
        )


@dataclass(frozen=True, slots=True)
class TrackerTransform:
    role: SemanticTrackerRole
    position: Vector3
    rotation: Quaternion


def _scale(vector: Vector3, amount: float) -> Vector3:
    return (
        vector[0] * amount,
        vector[1] * amount,
        vector[2] * amount,
    )


def synthetic_tracker_anchor_definitions(
    target_skeleton: SkeletonDefinition,
) -> Tuple[TrackerAnchorDefinition, ...]:
    """Return replaceable Phase 2C fixture anchors, not product defaults."""

    validate_rebocap24_skeleton(target_skeleton)
    left_foot_offset = _scale(
        target_skeleton.joint("L_Foot").rest_local_position, 0.5
    )
    right_foot_offset = _scale(
        target_skeleton.joint("R_Foot").rest_local_position, 0.5
    )
    left_upper_arm_offset = _scale(
        target_skeleton.joint("L_Elbow").rest_local_position, 0.5
    )
    right_upper_arm_offset = _scale(
        target_skeleton.joint("R_Elbow").rest_local_position, 0.5
    )
    identity = Quaternion.identity()
    return (
        TrackerAnchorDefinition(
            SemanticTrackerRole.HIP, "Pelvis", (0.0, 0.0, 0.04), identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.CHEST, "Spine3", (0.0, 0.05, 0.04), identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.LEFT_KNEE, "L_Knee", (0.0, 0.0, 0.03), identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.RIGHT_KNEE, "R_Knee", (0.0, 0.0, 0.03), identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.LEFT_FOOT, "L_Ankle", left_foot_offset, identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.RIGHT_FOOT, "R_Ankle", right_foot_offset, identity
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.LEFT_UPPER_ARM,
            "L_Shoulder",
            left_upper_arm_offset,
            identity,
        ),
        TrackerAnchorDefinition(
            SemanticTrackerRole.RIGHT_UPPER_ARM,
            "R_Shoulder",
            right_upper_arm_offset,
            identity,
        ),
    )


def build_tracker_transforms(
    target_pose: TargetPose,
    anchor_definitions: Sequence[TrackerAnchorDefinition],
) -> Tuple[TrackerTransform, ...]:
    """Build exactly one Quaternion transform for each semantic role."""

    definitions_by_role = {}
    for definition in anchor_definitions:
        if definition.role in definitions_by_role:
            raise ValueError(f"duplicate tracker role: {definition.role.value}")
        definitions_by_role[definition.role] = definition
    if set(definitions_by_role) != set(SEMANTIC_TRACKER_ROLES):
        raise ValueError("anchor definitions must contain exactly the 8 semantic roles")

    transforms = []
    for role in SEMANTIC_TRACKER_ROLES:
        definition = definitions_by_role[role]
        try:
            parent_transform = target_pose.transform(definition.parent_joint)
        except KeyError as error:
            raise ValueError(
                f"unknown anchor parent joint: {definition.parent_joint!r}"
            ) from error
        rotated_offset = rotate_vector(
            parent_transform.rotation, definition.local_position_offset
        )
        world_position = (
            parent_transform.position[0] + rotated_offset[0],
            parent_transform.position[1] + rotated_offset[1],
            parent_transform.position[2] + rotated_offset[2],
        )
        world_rotation = quaternion_multiply(
            parent_transform.rotation, definition.local_rotation_offset
        )
        transforms.append(TrackerTransform(role, world_position, world_rotation))
    return tuple(transforms)
