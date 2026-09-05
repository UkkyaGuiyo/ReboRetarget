"""Deterministic, side-effect-free target-skeleton retargeting and FK.

Quaternion convention
---------------------
Quaternions use Hamilton ``(w, x, y, z)`` components and active rotations.
``quaternion_multiply(left, right)`` represents ``left * right``: ``right``
is applied first, followed by ``left``.  Consequently::

    child_global = parent_global * child_local
    child_local = inverse(parent_global) * child_global

The module deliberately contains no device, network, process, filesystem, or
clock access.  It accepts already-constructed synthetic values and returns
immutable values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Optional, Sequence, Tuple, Union


Vector3 = Tuple[float, float, float]
QuaternionLike = Union["Quaternion", Sequence[float]]

_NORMAL_EPSILON = 1e-12
_ROOT_POSITION_EPSILON = 1e-12


REBOCAP_24_JOINT_NAMES: Tuple[str, ...] = (
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
    "L_Foot",
    "R_Foot",
    "Neck",
    "L_Collar",
    "R_Collar",
    "Head",
    "L_Shoulder",
    "R_Shoulder",
    "L_Elbow",
    "R_Elbow",
    "L_Wrist",
    "R_Wrist",
    "L_Hand",
    "R_Hand",
)

# Official ReboCap Unity SDK v4 and Unreal Engine plugin v2 encode the same
# parent relations.  The Unity root sentinel (-1) is normalized to None; the
# Unreal implementation represents the Pelvis root as self index 0.
REBOCAP_24_PARENT_INDICES: Tuple[int, ...] = (
    -1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8,
    9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21,
)
REBOCAP_24_PARENT_NAMES: Tuple[Optional[str], ...] = tuple(
    None if parent_index < 0 else REBOCAP_24_JOINT_NAMES[parent_index]
    for parent_index in REBOCAP_24_PARENT_INDICES
)


@dataclass(frozen=True, slots=True)
class HierarchySourceReference:
    """Public reference for the confirmed ReboCap parent array."""

    reference_id: str
    description: str
    location: str
    url: str
    sha256: Optional[str]


REBOCAP_HIERARCHY_SOURCE_REFERENCES: Tuple[HierarchySourceReference, ...] = (
    HierarchySourceReference(
        "REBOCAP_SDK_DOCS",
        "ReboCap official SDK documentation (SDK interface and 24 bone names)",
        "SDK Interface Description and 24 Bone Names; accessed 2026-09-04",
        "https://doc.rebocap.com/en_US/SDK/",
        None,
    ),
    HierarchySourceReference(
        "REBOCAP_UNITY_V4",
        "ReboCap official Unity SDK v4",
        "Assets/RebocapSdk/DemoScenes/SdkManager.cs:39-64 and "
        "Assets/RebocapSdk/RebocapWsSdk.cs:74-99",
        "https://doc.rebocap.com/img/files/rebocap_unity_sdk_v4.unitypackage",
        "E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF",
    ),
    HierarchySourceReference(
        "REBOCAP_UE_V2",
        "ReboCap official Unreal Engine plugin source v2",
        "Source/rebocap_runtime/Private/rebocap_source.cpp:115-152",
        "https://doc.rebocap.com/img/ue_plugin/rebocap_unreal_engine_plugin_v2.zip",
        "AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53",
    ),
)


@dataclass(frozen=True, slots=True)
class JointHierarchyEvidence:
    """Evidence classification for one normalized parent relation."""

    joint: str
    parent_index: int
    parent: Optional[str]
    status: str
    source_reference_ids: Tuple[str, ...]


REBOCAP_24_HIERARCHY_EVIDENCE: Tuple[JointHierarchyEvidence, ...] = tuple(
    JointHierarchyEvidence(
        joint,
        parent_index,
        parent,
        "CONFIRMED",
        (
            ("REBOCAP_SDK_DOCS", "REBOCAP_UNITY_V4", "REBOCAP_UE_V2")
            if parent_index < 0
            else ("REBOCAP_UNITY_V4", "REBOCAP_UE_V2")
        ),
    )
    for joint, parent_index, parent in zip(
        REBOCAP_24_JOINT_NAMES,
        REBOCAP_24_PARENT_INDICES,
        REBOCAP_24_PARENT_NAMES,
    )
)


def _finite_float(value: float, label: str) -> float:
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{label} must be finite")
    return converted


def _vector3(value: Sequence[float], label: str) -> Vector3:
    if len(value) != 3:
        raise ValueError(f"{label} must contain exactly 3 values")
    return (
        _finite_float(value[0], f"{label}[0]"),
        _finite_float(value[1], f"{label}[1]"),
        _finite_float(value[2], f"{label}[2]"),
    )


def _vector_length(value: Vector3) -> float:
    return math.sqrt(value[0] ** 2 + value[1] ** 2 + value[2] ** 2)


def _vector_add(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Hamilton quaternion stored as ``(w, x, y, z)``."""

    w: float
    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "w", _finite_float(self.w, "quaternion.w"))
        object.__setattr__(self, "x", _finite_float(self.x, "quaternion.x"))
        object.__setattr__(self, "y", _finite_float(self.y, "quaternion.y"))
        object.__setattr__(self, "z", _finite_float(self.z, "quaternion.z"))

    @staticmethod
    def identity() -> "Quaternion":
        return Quaternion(1.0, 0.0, 0.0, 0.0)

    def normalized(self) -> "Quaternion":
        magnitude = math.sqrt(
            self.w * self.w
            + self.x * self.x
            + self.y * self.y
            + self.z * self.z
        )
        if magnitude <= _NORMAL_EPSILON:
            raise ValueError("quaternion magnitude must be non-zero")
        if magnitude == 1.0:
            return self
        if not math.isfinite(magnitude):
            # Finite components can overflow the sum of squares. Scale only
            # that exceptional path, keeping ordinary normalization unchanged.
            scale = max(abs(self.w), abs(self.x), abs(self.y), abs(self.z))
            scaled = (self.w / scale, self.x / scale, self.y / scale, self.z / scale)
            scaled_magnitude = math.sqrt(sum(value * value for value in scaled))
            return Quaternion(*(value / scaled_magnitude for value in scaled))
        return Quaternion(
            self.w / magnitude,
            self.x / magnitude,
            self.y / magnitude,
            self.z / magnitude,
        )

    def negated(self) -> "Quaternion":
        return Quaternion(-self.w, -self.x, -self.y, -self.z)


def _quaternion(value: QuaternionLike, label: str) -> Quaternion:
    if isinstance(value, Quaternion):
        return value.normalized()
    if len(value) != 4:
        raise ValueError(f"{label} must contain exactly 4 values in (w,x,y,z) order")
    return Quaternion(value[0], value[1], value[2], value[3]).normalized()


def quaternion_multiply(left: QuaternionLike, right: QuaternionLike) -> Quaternion:
    """Return Hamilton ``left * right`` (apply ``right``, then ``left``)."""

    a = _quaternion(left, "left quaternion")
    b = _quaternion(right, "right quaternion")
    return Quaternion(
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    ).normalized()


def quaternion_inverse(value: QuaternionLike) -> Quaternion:
    """Return the inverse of a rotation quaternion."""

    q = _quaternion(value, "quaternion")
    return Quaternion(q.w, -q.x, -q.y, -q.z)


def quaternion_from_axis_angle(axis: Sequence[float], degrees: float) -> Quaternion:
    """Create an active rotation from an axis and an angle in degrees."""

    vector = _vector3(axis, "axis")
    length = _vector_length(vector)
    if length <= _NORMAL_EPSILON:
        raise ValueError("axis magnitude must be non-zero")
    angle = math.radians(_finite_float(degrees, "degrees")) * 0.5
    sine = math.sin(angle) / length
    return Quaternion(
        math.cos(angle),
        vector[0] * sine,
        vector[1] * sine,
        vector[2] * sine,
    ).normalized()


def rotate_vector(rotation: QuaternionLike, vector: Sequence[float]) -> Vector3:
    """Actively rotate a three-dimensional vector."""

    q = _quaternion(rotation, "rotation")
    v = _vector3(vector, "vector")
    # Expanded q * (0, v) * inverse(q); avoids normalizing the pure-vector
    # quaternion, which would incorrectly discard the vector magnitude.
    ux, uy, uz = q.x, q.y, q.z
    dot_uv = ux * v[0] + uy * v[1] + uz * v[2]
    dot_uu = ux * ux + uy * uy + uz * uz
    cross_x = uy * v[2] - uz * v[1]
    cross_y = uz * v[0] - ux * v[2]
    cross_z = ux * v[1] - uy * v[0]
    scale = q.w * q.w - dot_uu
    return (
        scale * v[0] + 2.0 * dot_uv * ux + 2.0 * q.w * cross_x,
        scale * v[1] + 2.0 * dot_uv * uy + 2.0 * q.w * cross_y,
        scale * v[2] + 2.0 * dot_uv * uz + 2.0 * q.w * cross_z,
    )


def quaternions_equivalent(
    left: QuaternionLike,
    right: QuaternionLike,
    *,
    tolerance: float = 1e-9,
) -> bool:
    """Compare rotations while treating ``q`` and ``-q`` as equivalent."""

    if tolerance < 0.0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    a = _quaternion(left, "left quaternion")
    b = _quaternion(right, "right quaternion")
    dot = abs(a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z)
    return 1.0 - min(1.0, dot) <= tolerance


def quaternion_rotation_angle_degrees(value: QuaternionLike) -> float:
    """Return the shortest represented rotation angle in ``[0, 180]``."""

    q = _quaternion(value, "quaternion")
    return math.degrees(2.0 * math.acos(min(1.0, abs(q.w))))


@dataclass(frozen=True, slots=True)
class JointDefinition:
    """One joint's immutable rest transform relative to its parent.

    ``segment_length`` is derived from ``rest_local_position`` so the two
    values cannot disagree.
    """

    name: str
    parent: Optional[str]
    rest_local_position: Vector3
    rest_local_rotation: Quaternion = field(default_factory=Quaternion.identity)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("joint name must be a non-empty string")
        if self.parent is not None and (not isinstance(self.parent, str) or not self.parent):
            raise ValueError("joint parent must be None or a non-empty string")
        object.__setattr__(
            self,
            "rest_local_position",
            _vector3(self.rest_local_position, f"{self.name}.rest_local_position"),
        )
        object.__setattr__(
            self,
            "rest_local_rotation",
            _quaternion(self.rest_local_rotation, f"{self.name}.rest_local_rotation"),
        )

    @property
    def segment_length(self) -> float:
        return _vector_length(self.rest_local_position)


@dataclass(frozen=True, slots=True)
class SkeletonDefinition:
    """A single-root, parent-before-child skeleton definition."""

    joints: Tuple[JointDefinition, ...]

    def __post_init__(self) -> None:
        joints = tuple(self.joints)
        if not joints:
            raise ValueError("skeleton must contain at least one joint")

        names = [joint.name for joint in joints]
        if len(names) != len(set(names)):
            raise ValueError("joint names must be unique")
        roots = [joint for joint in joints if joint.parent is None]
        if len(roots) != 1 or joints[0].parent is not None:
            raise ValueError("skeleton must have exactly one root at index 0")
        if joints[0].segment_length > _ROOT_POSITION_EPSILON:
            raise ValueError("root rest_local_position must be (0,0,0)")

        seen = set()
        for joint in joints:
            if joint.parent is not None and joint.parent not in seen:
                raise ValueError(
                    f"parent {joint.parent!r} must appear before joint {joint.name!r}"
                )
            seen.add(joint.name)
        object.__setattr__(self, "joints", joints)

    @property
    def joint_names(self) -> Tuple[str, ...]:
        return tuple(joint.name for joint in self.joints)

    def index(self, name: str) -> int:
        try:
            return self.joint_names.index(name)
        except ValueError as error:
            raise KeyError(name) from error

    def joint(self, name: str) -> JointDefinition:
        return self.joints[self.index(name)]


def validate_rebocap24_skeleton(skeleton: SkeletonDefinition) -> None:
    """Validate the confirmed ReboCap 24-joint order and parent hierarchy."""

    if skeleton.joint_names != REBOCAP_24_JOINT_NAMES:
        raise ValueError("skeleton joint order does not match ReboCap's 24-joint order")
    actual_parents = tuple(joint.parent for joint in skeleton.joints)
    if actual_parents != REBOCAP_24_PARENT_NAMES:
        raise ValueError(
            "skeleton parent hierarchy does not match ReboCap's 24-joint hierarchy"
        )


@dataclass(frozen=True, slots=True)
class SourcePose:
    """Pelvis translation plus core-internal global joint rotations.

    The official SDK's global values are rotations relative to its T-pose,
    not fully composed target-world bind rotations. ``from_rebocap24`` only
    validates the ordered value container; a live semantic adapter is not yet
    implemented and must make that T-pose-delta boundary explicit.
    """

    root_translation: Vector3
    global_rotations: Tuple[Quaternion, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "root_translation",
            _vector3(self.root_translation, "root_translation"),
        )
        rotations = tuple(
            _quaternion(rotation, f"global_rotations[{index}]")
            for index, rotation in enumerate(self.global_rotations)
        )
        if not rotations:
            raise ValueError("source pose must contain at least one rotation")
        object.__setattr__(self, "global_rotations", rotations)

    @classmethod
    def from_rebocap24(
        cls,
        root_translation: Sequence[float],
        global_rotations_wxyz: Sequence[QuaternionLike],
    ) -> "SourcePose":
        """Validate and contain the confirmed ordered 24-Quaternion shape.

        This does not implement the live ReboCap T-pose-delta adapter.
        """

        if len(global_rotations_wxyz) != len(REBOCAP_24_JOINT_NAMES):
            raise ValueError("ReboCap pose must contain exactly 24 global rotations")
        rotations = tuple(
            _quaternion(value, f"global_rotations_wxyz[{index}]")
            for index, value in enumerate(global_rotations_wxyz)
        )
        return cls(_vector3(root_translation, "root_translation"), rotations)


@dataclass(frozen=True, slots=True)
class Transform:
    position: Vector3
    rotation: Quaternion


@dataclass(frozen=True, slots=True)
class JointDiagnostic:
    name: str
    source_local_rotation: Quaternion
    local_rotation_magnitude_degrees: float


@dataclass(frozen=True, slots=True)
class TargetPose:
    joint_names: Tuple[str, ...]
    local_rotations: Tuple[Quaternion, ...]
    world_transforms: Tuple[Transform, ...]
    diagnostics: Tuple[JointDiagnostic, ...]

    def transform(self, name: str) -> Transform:
        try:
            return self.world_transforms[self.joint_names.index(name)]
        except ValueError as error:
            raise KeyError(name) from error

    def local_rotation(self, name: str) -> Quaternion:
        try:
            return self.local_rotations[self.joint_names.index(name)]
        except ValueError as error:
            raise KeyError(name) from error

    def diagnostic(self, name: str) -> JointDiagnostic:
        try:
            return self.diagnostics[self.joint_names.index(name)]
        except ValueError as error:
            raise KeyError(name) from error


def global_to_local_rotations(
    skeleton: SkeletonDefinition,
    global_rotations: Sequence[QuaternionLike],
) -> Tuple[Quaternion, ...]:
    """Recover locals using ``inverse(parent_global) * child_global``."""

    if len(global_rotations) != len(skeleton.joints):
        raise ValueError("global rotation count must match skeleton joint count")
    globals_normalized = tuple(
        _quaternion(value, f"global_rotations[{index}]")
        for index, value in enumerate(global_rotations)
    )
    indices = {joint.name: index for index, joint in enumerate(skeleton.joints)}
    local_rotations = []
    for index, joint in enumerate(skeleton.joints):
        child_global = globals_normalized[index]
        if joint.parent is None:
            local_rotations.append(child_global)
            continue
        parent_global = globals_normalized[indices[joint.parent]]
        local_rotations.append(
            quaternion_multiply(quaternion_inverse(parent_global), child_global)
        )
    return tuple(local_rotations)


def forward_kinematics(
    skeleton: SkeletonDefinition,
    root_position: Sequence[float],
    local_rotations: Sequence[QuaternionLike],
) -> Tuple[Transform, ...]:
    """Build world transforms using only the target skeleton's rest vectors."""

    if len(local_rotations) != len(skeleton.joints):
        raise ValueError("local rotation count must match skeleton joint count")
    root = _vector3(root_position, "root_position")
    locals_normalized = tuple(
        _quaternion(value, f"local_rotations[{index}]")
        for index, value in enumerate(local_rotations)
    )
    indices = {joint.name: index for index, joint in enumerate(skeleton.joints)}
    world = []
    for index, joint in enumerate(skeleton.joints):
        local_rotation = locals_normalized[index]
        if joint.parent is None:
            world.append(Transform(root, local_rotation))
            continue
        parent = world[indices[joint.parent]]
        world.append(
            Transform(
                _vector_add(
                    parent.position,
                    rotate_vector(parent.rotation, joint.rest_local_position),
                ),
                quaternion_multiply(parent.rotation, local_rotation),
            )
        )
    return tuple(world)


def _assert_matching_semantics(
    source_skeleton: SkeletonDefinition,
    target_skeleton: SkeletonDefinition,
) -> None:
    if set(source_skeleton.joint_names) != set(target_skeleton.joint_names):
        raise ValueError("source and target skeletons must contain the same joint names")
    source_parents = {joint.name: joint.parent for joint in source_skeleton.joints}
    for target_joint in target_skeleton.joints:
        if source_parents[target_joint.name] != target_joint.parent:
            raise ValueError(
                f"source and target parent differ for joint {target_joint.name!r}"
            )


def retarget_pose(
    source_pose: SourcePose,
    source_skeleton: SkeletonDefinition,
    target_skeleton: SkeletonDefinition,
) -> TargetPose:
    """Transfer local motion deltas to the target rest skeleton, then run FK.

    For every semantic joint::

        source_local = inverse(source_parent_global) * source_child_global
        motion_delta = inverse(source_rest_local) * source_local
        target_local = target_rest_local * motion_delta

    Positions come solely from the target's rest-local vectors and root
    translation.  Source bone lengths and source joint positions are not copied.
    """

    if len(source_pose.global_rotations) != len(source_skeleton.joints):
        raise ValueError("source pose rotation count must match source skeleton")
    _assert_matching_semantics(source_skeleton, target_skeleton)

    source_locals = global_to_local_rotations(
        source_skeleton, source_pose.global_rotations
    )
    source_local_by_name = dict(zip(source_skeleton.joint_names, source_locals))
    source_joint_by_name = {
        joint.name: joint for joint in source_skeleton.joints
    }

    target_locals = []
    diagnostics = []
    for target_joint in target_skeleton.joints:
        source_local = source_local_by_name[target_joint.name]
        source_joint = source_joint_by_name[target_joint.name]
        motion_delta = quaternion_multiply(
            quaternion_inverse(source_joint.rest_local_rotation), source_local
        )
        target_locals.append(
            quaternion_multiply(target_joint.rest_local_rotation, motion_delta)
        )

        magnitude = quaternion_rotation_angle_degrees(source_local)
        diagnostics.append(
            JointDiagnostic(
                target_joint.name,
                source_local,
                magnitude,
            )
        )

    target_local_tuple = tuple(target_locals)
    world = forward_kinematics(
        target_skeleton, source_pose.root_translation, target_local_tuple
    )
    return TargetPose(
        target_skeleton.joint_names,
        target_local_tuple,
        world,
        tuple(diagnostics),
    )


def retarget_sequence(
    source_poses: Sequence[SourcePose],
    source_skeleton: SkeletonDefinition,
    target_skeleton: SkeletonDefinition,
) -> Tuple[TargetPose, ...]:
    """Retarget an in-memory sequence without timing, I/O, or interpolation."""

    return tuple(
        retarget_pose(source_pose, source_skeleton, target_skeleton)
        for source_pose in source_poses
    )


def leg_lengths_from_controls(
    source_upper_leg: float,
    source_lower_leg: float,
    *,
    leg_length: float = 1.0,
    thigh_calf_balance: float = 0.0,
) -> Tuple[float, float]:
    """Convert user-meaningful leg controls to target segment lengths.

    ``leg_length`` scales the *total* source leg length.  Thus ``1.10`` makes
    the target total exactly 10% longer.  ``thigh_calf_balance`` is an additive
    shift in the thigh's share of that fixed total: ``+0.05`` transfers five
    percentage points from calf to thigh without changing total length.
    """

    upper = _finite_float(source_upper_leg, "source_upper_leg")
    lower = _finite_float(source_lower_leg, "source_lower_leg")
    scale = _finite_float(leg_length, "leg_length")
    balance = _finite_float(thigh_calf_balance, "thigh_calf_balance")
    if upper <= 0.0 or lower <= 0.0:
        raise ValueError("source leg segment lengths must be positive")
    if scale <= 0.0:
        raise ValueError("leg_length must be positive")

    source_total = upper + lower
    target_total = source_total * scale
    thigh_share = upper / source_total + balance
    if not 0.0 < thigh_share < 1.0:
        raise ValueError("thigh_calf_balance must leave both segments positive")
    target_upper = target_total * thigh_share
    return (target_upper, target_total - target_upper)


def arm_lengths_from_controls(
    source_upper_arm: float,
    source_forearm: float,
    *,
    arm_length: float = 1.0,
    upper_arm_forearm_balance: float = 0.0,
) -> Tuple[float, float]:
    """Return target upper-arm/forearm lengths, excluding shoulder and hand.

    ``arm_length`` scales their total; balance adds to the upper arm's share
    of that scaled total (0.05 means five percentage points, not five percent
    of the upper arm). This is pure geometry, not controller or IK fitting.
    """
    upper = _finite_float(source_upper_arm, "source_upper_arm")
    lower = _finite_float(source_forearm, "source_forearm")
    scale = _finite_float(arm_length, "arm_length")
    balance = _finite_float(upper_arm_forearm_balance, "upper_arm_forearm_balance")
    if upper <= 0.0 or lower <= 0.0 or scale <= 0.0:
        raise ValueError("arm segment lengths and scale must be positive")
    total = _finite_float(upper + lower, "source arm total")
    target_total = _finite_float(total * scale, "target arm total")
    share = upper / total + balance
    if not 0.0 < share < 1.0:
        raise ValueError("upper_arm_forearm_balance must leave both segments positive")
    target_upper = target_total * share
    target_lower = target_total - target_upper
    if target_upper <= 0.0 or target_lower <= 0.0:
        raise ValueError("target arm segments must remain representably positive")
    return target_upper, target_lower
