"""Pure VRChat OSC tracker representation and minimal OSC 1.0 codec.

This module stops at in-memory values and bytes.  It contains no socket,
network, process, filesystem, clock, scheduling, or live-SDK access.

VRChat tracker rotations are Euler angles in degrees, applied about fixed
world axes in Z, X, Y order.  With this repository's Hamilton active
Quaternion convention, reconstruction is ``qY * qX * qZ``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Optional, Sequence, Tuple

from .fk import (
    Quaternion,
    QuaternionLike,
    Vector3,
    quaternion_from_axis_angle,
    quaternion_multiply,
    rotate_vector,
)
from .tracker_anchors import (
    SEMANTIC_TRACKER_ROLES,
    SemanticTrackerRole,
    TrackerTransform,
)


VRCHAT_BODY_TRACKER_SLOT_MIN = 1
VRCHAT_BODY_TRACKER_SLOT_MAX = 8
OSC_FLOAT3_TYPE_TAG = ",fff"
HEAD_POSITION_ADDRESS = "/tracking/trackers/head/position"
HEAD_ROTATION_ADDRESS = "/tracking/trackers/head/rotation"

_GIMBAL_EPSILON = 1e-10


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


def _quaternion(value: QuaternionLike, label: str) -> Quaternion:
    try:
        components = (
            (value.w, value.x, value.y, value.z)
            if isinstance(value, Quaternion)
            else tuple(value)
        )
        return Quaternion(*components).normalized()
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{label} must be a finite non-zero (w,x,y,z) quaternion"
        ) from error


def _body_tracker_slot(value: int, label: str = "slot") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer from 1 through 8")
    if not VRCHAT_BODY_TRACKER_SLOT_MIN <= value <= VRCHAT_BODY_TRACKER_SLOT_MAX:
        raise ValueError(f"{label} must be in the inclusive range 1 through 8")
    return value


def _osc_address(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("/"):
        raise ValueError("OSC address must be a string beginning with '/'")
    if "\0" in value:
        raise ValueError("OSC address must not contain a NUL character")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("OSC address must contain only ASCII characters") from error
    return value


@dataclass(frozen=True, slots=True)
class TrackerSlotMapping:
    """One configurable semantic-role to numbered-transport-slot mapping."""

    role: SemanticTrackerRole
    slot: int

    def __post_init__(self) -> None:
        if not isinstance(self.role, SemanticTrackerRole):
            raise ValueError("role must be a SemanticTrackerRole")
        object.__setattr__(self, "slot", _body_tracker_slot(self.slot))


DEFAULT_TRACKER_SLOT_MAPPINGS: Tuple[TrackerSlotMapping, ...] = (
    TrackerSlotMapping(SemanticTrackerRole.HIP, 1),
    TrackerSlotMapping(SemanticTrackerRole.CHEST, 2),
    TrackerSlotMapping(SemanticTrackerRole.LEFT_KNEE, 3),
    TrackerSlotMapping(SemanticTrackerRole.RIGHT_KNEE, 4),
    TrackerSlotMapping(SemanticTrackerRole.LEFT_FOOT, 5),
    TrackerSlotMapping(SemanticTrackerRole.RIGHT_FOOT, 6),
    TrackerSlotMapping(SemanticTrackerRole.LEFT_UPPER_ARM, 7),
    TrackerSlotMapping(SemanticTrackerRole.RIGHT_UPPER_ARM, 8),
)


def validate_tracker_slot_mappings(
    mappings: Sequence[TrackerSlotMapping],
) -> Tuple[TrackerSlotMapping, ...]:
    """Require each of the eight roles and slots exactly once."""

    values = tuple(mappings)
    for mapping in values:
        if not isinstance(mapping, TrackerSlotMapping):
            raise ValueError("mappings must contain TrackerSlotMapping values")
    roles = tuple(mapping.role for mapping in values)
    slots = tuple(mapping.slot for mapping in values)
    if len(roles) != len(set(roles)):
        raise ValueError("tracker slot mappings contain a duplicate semantic role")
    if len(slots) != len(set(slots)):
        raise ValueError("tracker slot mappings contain a duplicate slot")
    if set(roles) != set(SEMANTIC_TRACKER_ROLES):
        raise ValueError(
            "tracker slot mappings must contain exactly the 8 semantic roles"
        )
    if set(slots) != set(
        range(VRCHAT_BODY_TRACKER_SLOT_MIN, VRCHAT_BODY_TRACKER_SLOT_MAX + 1)
    ):
        raise ValueError(
            "tracker slot mappings must contain every slot from 1 through 8"
        )
    return values


@dataclass(frozen=True, slots=True)
class OscTrackerPose:
    """One body tracker's network-independent VRChat output representation."""

    slot: int
    position_xyz_m: Vector3
    rotation_euler_xyz_deg: Vector3

    def __post_init__(self) -> None:
        object.__setattr__(self, "slot", _body_tracker_slot(self.slot))
        object.__setattr__(
            self,
            "position_xyz_m",
            _vector3(self.position_xyz_m, "position_xyz_m"),
        )
        object.__setattr__(
            self,
            "rotation_euler_xyz_deg",
            _vector3(self.rotation_euler_xyz_deg, "rotation_euler_xyz_deg"),
        )


@dataclass(frozen=True, slots=True)
class OscFloat3Message:
    """An OSC address and the only payload shape required by Phase 2D."""

    address: str
    values: Vector3

    def __post_init__(self) -> None:
        object.__setattr__(self, "address", _osc_address(self.address))
        object.__setattr__(self, "values", _vector3(self.values, "values"))


@dataclass(frozen=True, slots=True)
class TrackingSpaceAlignment:
    """Rigid Source-tracking-space to VRChat-tracking-space alignment.

    Phase 2D deliberately implements only translation and yaw.  This is not
    ReboCap calibration, VRChat FBT calibration, head alignment, SteamVR
    playspace recentering, or a general recenter operation.
    """

    translation_xyz_m: Vector3 = (0.0, 0.0, 0.0)
    yaw_degrees: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "translation_xyz_m",
            _vector3(self.translation_xyz_m, "translation_xyz_m"),
        )
        object.__setattr__(
            self, "yaw_degrees", _finite_float(self.yaw_degrees, "yaw_degrees")
        )


@dataclass(frozen=True, slots=True)
class HeadAlignmentReference:
    """Optional VRChat head-alignment values, separate from body slots."""

    position_xyz_m: Optional[Vector3] = None
    rotation: Optional[Quaternion] = None

    def __post_init__(self) -> None:
        if self.position_xyz_m is None and self.rotation is None:
            raise ValueError("head alignment requires a position or rotation")
        if self.position_xyz_m is not None:
            object.__setattr__(
                self,
                "position_xyz_m",
                _vector3(self.position_xyz_m, "position_xyz_m"),
            )
        if self.rotation is not None:
            object.__setattr__(
                self,
                "rotation",
                _quaternion(self.rotation, "rotation"),
            )


def _normalize_degrees(value: float) -> float:
    normalized = (value + 180.0) % 360.0 - 180.0
    return 0.0 if abs(normalized) < 1e-12 else normalized


def quaternion_to_vrchat_euler_degrees(rotation: QuaternionLike) -> Vector3:
    """Convert to VRChat's degree Euler representation for fixed Z-X-Y axes.

    The returned X branch is in ``[-90, 90]`` and Y/Z are normalized to
    ``[-180, 180)``.  At gimbal singularity, Z is deterministically set to
    zero and Y carries the equivalent remaining rotation.
    """

    q = _quaternion(rotation, "rotation")
    ww, xx, yy, zz = q.w * q.w, q.x * q.x, q.y * q.y, q.z * q.z
    xy, xz, yz = q.x * q.y, q.x * q.z, q.y * q.z
    wx, wy, wz = q.w * q.x, q.w * q.y, q.w * q.z
    matrix = (
        (ww + xx - yy - zz, 2.0 * (xy - wz), 2.0 * (xz + wy)),
        (2.0 * (xy + wz), ww - xx + yy - zz, 2.0 * (yz - wx)),
        (2.0 * (xz - wy), 2.0 * (yz + wx), ww - xx - yy + zz),
    )

    sin_x = max(-1.0, min(1.0, -matrix[1][2]))
    x_radians = math.asin(sin_x)
    cos_x = math.cos(x_radians)
    if abs(cos_x) > _GIMBAL_EPSILON:
        y_radians = math.atan2(matrix[0][2], matrix[2][2])
        z_radians = math.atan2(matrix[1][0], matrix[1][1])
    elif sin_x >= 0.0:
        y_radians = math.atan2(matrix[0][1], matrix[0][0])
        z_radians = 0.0
    else:
        y_radians = math.atan2(-matrix[0][1], matrix[0][0])
        z_radians = 0.0

    return (
        _normalize_degrees(math.degrees(x_radians)),
        _normalize_degrees(math.degrees(y_radians)),
        _normalize_degrees(math.degrees(z_radians)),
    )


def vrchat_euler_degrees_to_quaternion(
    rotation_euler_xyz_deg: Sequence[float],
) -> Quaternion:
    """Reconstruct VRChat's fixed-axis Z-X-Y application as ``qY*qX*qZ``."""

    x_degrees, y_degrees, z_degrees = _vector3(
        rotation_euler_xyz_deg, "rotation_euler_xyz_deg"
    )
    qx = quaternion_from_axis_angle((1.0, 0.0, 0.0), x_degrees)
    qy = quaternion_from_axis_angle((0.0, 1.0, 0.0), y_degrees)
    qz = quaternion_from_axis_angle((0.0, 0.0, 1.0), z_degrees)
    return quaternion_multiply(qy, quaternion_multiply(qx, qz))


def apply_tracking_space_alignment(
    tracker_transforms: Sequence[TrackerTransform],
    alignment: TrackingSpaceAlignment,
) -> Tuple[TrackerTransform, ...]:
    """Apply one yaw and translation rigid transform to every tracker."""

    if not isinstance(alignment, TrackingSpaceAlignment):
        raise ValueError("alignment must be a TrackingSpaceAlignment")
    yaw = quaternion_from_axis_angle((0.0, 1.0, 0.0), alignment.yaw_degrees)
    aligned = []
    for tracker in tracker_transforms:
        if not isinstance(tracker, TrackerTransform):
            raise ValueError("tracker_transforms must contain TrackerTransform values")
        rotated_position = rotate_vector(yaw, tracker.position)
        translated_position = tuple(
            rotated + translation
            for rotated, translation in zip(
                rotated_position, alignment.translation_xyz_m
            )
        )
        aligned.append(
            TrackerTransform(
                tracker.role,
                translated_position,
                quaternion_multiply(yaw, tracker.rotation),
            )
        )
    return tuple(aligned)


def build_osc_tracker_poses(
    tracker_transforms: Sequence[TrackerTransform],
    mappings: Sequence[TrackerSlotMapping] = DEFAULT_TRACKER_SLOT_MAPPINGS,
) -> Tuple[OscTrackerPose, ...]:
    """Map exactly eight semantic transforms to deterministic numbered slots."""

    validated_mappings = validate_tracker_slot_mappings(mappings)
    transforms_by_role = {}
    for transform in tracker_transforms:
        if not isinstance(transform, TrackerTransform):
            raise ValueError("tracker_transforms must contain TrackerTransform values")
        if transform.role in transforms_by_role:
            raise ValueError(f"duplicate tracker role: {transform.role.value}")
        transforms_by_role[transform.role] = transform
    if set(transforms_by_role) != set(SEMANTIC_TRACKER_ROLES):
        raise ValueError("tracker transforms must contain exactly the 8 semantic roles")

    slot_by_role = {mapping.role: mapping.slot for mapping in validated_mappings}
    poses = (
        OscTrackerPose(
            slot_by_role[role],
            transforms_by_role[role].position,
            quaternion_to_vrchat_euler_degrees(transforms_by_role[role].rotation),
        )
        for role in SEMANTIC_TRACKER_ROLES
    )
    return tuple(sorted(poses, key=lambda pose: pose.slot))


def tracker_position_address(slot: int) -> str:
    return f"/tracking/trackers/{_body_tracker_slot(slot)}/position"


def tracker_rotation_address(slot: int) -> str:
    return f"/tracking/trackers/{_body_tracker_slot(slot)}/rotation"


def build_tracker_messages(
    tracker_poses: Sequence[OscTrackerPose],
) -> Tuple[OscFloat3Message, ...]:
    """Build two in-memory OSC messages per slot; no transmission occurs."""

    poses = tuple(tracker_poses)
    for pose in poses:
        if not isinstance(pose, OscTrackerPose):
            raise ValueError("tracker_poses must contain OscTrackerPose values")
    slots = tuple(pose.slot for pose in poses)
    if len(slots) != len(set(slots)):
        raise ValueError("tracker poses contain a duplicate slot")
    if set(slots) != set(
        range(VRCHAT_BODY_TRACKER_SLOT_MIN, VRCHAT_BODY_TRACKER_SLOT_MAX + 1)
    ):
        raise ValueError("tracker poses must contain every slot from 1 through 8")

    messages = []
    for pose in sorted(poses, key=lambda value: value.slot):
        messages.append(
            OscFloat3Message(
                tracker_position_address(pose.slot), pose.position_xyz_m
            )
        )
        messages.append(
            OscFloat3Message(
                tracker_rotation_address(pose.slot), pose.rotation_euler_xyz_deg
            )
        )
    return tuple(messages)


def build_head_alignment_messages(
    reference: HeadAlignmentReference,
) -> Tuple[OscFloat3Message, ...]:
    """Build separate head-alignment messages without stream/timing behavior."""

    if not isinstance(reference, HeadAlignmentReference):
        raise ValueError("reference must be a HeadAlignmentReference")
    messages = []
    if reference.position_xyz_m is not None:
        messages.append(
            OscFloat3Message(HEAD_POSITION_ADDRESS, reference.position_xyz_m)
        )
    if reference.rotation is not None:
        messages.append(
            OscFloat3Message(
                HEAD_ROTATION_ADDRESS,
                quaternion_to_vrchat_euler_degrees(reference.rotation),
            )
        )
    return tuple(messages)


def _encode_osc_string(value: str) -> bytes:
    encoded = value.encode("ascii") + b"\0"
    return encoded + b"\0" * ((-len(encoded)) % 4)


def encode_osc_float3_message(message: OscFloat3Message) -> bytes:
    """Encode one OSC 1.0 address, ``,fff`` tag, and three float32 values."""

    if not isinstance(message, OscFloat3Message):
        raise ValueError("message must be an OscFloat3Message")
    try:
        payload = struct.pack(">fff", *message.values)
    except OverflowError as error:
        raise ValueError("OSC values must fit finite IEEE 754 float32") from error
    return (
        _encode_osc_string(message.address)
        + _encode_osc_string(OSC_FLOAT3_TYPE_TAG)
        + payload
    )


def _decode_osc_string(packet: bytes, offset: int, label: str) -> Tuple[str, int]:
    try:
        nul_index = packet.index(0, offset)
    except ValueError as error:
        raise ValueError(f"{label} is not NUL-terminated") from error
    padded_end = ((nul_index + 1 + 3) // 4) * 4
    if padded_end > len(packet):
        raise ValueError(f"{label} padding extends past the packet")
    if any(packet[nul_index:padded_end]):
        raise ValueError(f"{label} padding must contain only NUL bytes")
    try:
        decoded = packet[offset:nul_index].decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} must contain only ASCII characters") from error
    return decoded, padded_end


def decode_osc_float3_message(packet: bytes) -> OscFloat3Message:
    """Strictly decode the Phase 2D OSC subset back into an immutable value."""

    if not isinstance(packet, (bytes, bytearray, memoryview)):
        raise ValueError("packet must be bytes-like")
    encoded = bytes(packet)
    address, offset = _decode_osc_string(encoded, 0, "OSC address")
    type_tag, offset = _decode_osc_string(encoded, offset, "OSC type tag")
    if type_tag != OSC_FLOAT3_TYPE_TAG:
        raise ValueError("OSC type tag must be exactly ',fff'")
    if len(encoded) - offset != 12:
        raise ValueError("OSC float3 payload must contain exactly 12 bytes")
    values = struct.unpack(">fff", encoded[offset:])
    if not all(math.isfinite(value) for value in values):
        raise ValueError("OSC float3 payload must contain only finite values")
    return OscFloat3Message(address, values)
