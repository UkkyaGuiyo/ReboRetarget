"""Pure, bounded known-motion comparisons; never writes or retains raw frames.

Callers own cue timing and RAM windows. A numeric PASS supports the supplied
cue marker, not anatomical truth or physical sensor ownership. Thresholds are
conservative detectable-response floors, never requested body displacement.
"""

from dataclasses import dataclass
import math
from typing import Sequence

from reboretarget.fk import (
    Quaternion, SourcePose, SkeletonDefinition, REBOCAP_24_JOINT_NAMES,
    quaternion_inverse, quaternion_multiply, rotate_vector,
    global_to_local_rotations, validate_rebocap24_skeleton,
)
from reboretarget.rebocap_adapter import ReboCapDeltaPose, source_bind_global_rotations
from reboretarget.tracker_anchors import TrackerTransform, SEMANTIC_TRACKER_ROLES

CUES = ("right", "forward", "crouch", "left_knee", "right_knee", "yaw_left",
        "yaw_right", "left_arm", "right_arm", "left_shoulder", "right_shoulder")
ANALYSIS_LIMITS = {
    "baseline_count": 60, "held_count": 20, "returned_count": 20,
    "noise_multiplier": 3.0, "translation_floor_m": 0.02,
    "rotation_floor_deg": 3.0, "dominance_ratio": 2.0,
    "return_fraction": 0.35, "adapter_tolerance_deg": 0.0001,
}
_PAIRS = (("L_Shoulder", "L_Elbow"), ("R_Shoulder", "R_Elbow"),
          ("L_Ankle", "L_Foot"), ("R_Ankle", "R_Foot"),
          ("L_Wrist", "L_Hand"), ("R_Wrist", "R_Hand"))


@dataclass(frozen=True, slots=True)
class MotionFrame:
    """One RAM-only, same-sequence pipeline observation (no timestamp/ID)."""

    delta_pose: ReboCapDeltaPose
    canonical: SourcePose
    anchors: tuple[TrackerTransform, ...]

    def __post_init__(self):
        if len(self.canonical.global_rotations) != 24:
            raise ValueError("canonical requires 24 joints")
        anchors = tuple(self.anchors)
        if len(anchors) != 8 or {a.role for a in anchors} != set(SEMANTIC_TRACKER_ROLES):
            raise ValueError("exactly eight unique semantic anchors required")
        for anchor in anchors:
            if len(anchor.position) != 3 or not all(math.isfinite(v) for v in anchor.position):
                raise ValueError("finite anchor position required")
            anchor.rotation.normalized()
        object.__setattr__(self, "anchors", anchors)


def relative_rotation(before: Quaternion, after: Quaternion) -> Quaternion:
    """World-space change: after * inverse(before), invariant under q sign."""
    q = quaternion_multiply(after, quaternion_inverse(before))
    # Deterministic tie at 180 degrees as well as ordinary hemisphere alignment.
    for value in (q.w, q.x, q.y, q.z):
        if abs(value) > 1e-12:
            return q.negated() if value < 0 else q
    return q


def axis_angle(before: Quaternion, after: Quaternion) -> dict:
    q = relative_rotation(before, after)
    length = math.sqrt(q.x*q.x + q.y*q.y + q.z*q.z)
    angle = math.degrees(2 * math.atan2(length, max(0.0, q.w)))
    return {"angle_deg": angle,
            "axis_xyz": [q.x/length, q.y/length, q.z/length] if length > 1e-12 else [0., 0., 0.]}


def rotation_distance(before: Quaternion, after: Quaternion) -> float:
    return axis_angle(before, after)["angle_deg"]


def _mean_q(values):
    first = values[0].normalized()
    components = []
    for value in values:
        q = value.normalized()
        if first.w*q.w + first.x*q.x + first.y*q.y + first.z*q.z < 0:
            q = q.negated()
        components.append((q.w, q.x, q.y, q.z))
    return Quaternion(*(sum(row[i] for row in components)/len(values) for i in range(4))).normalized()


def _mean_v(values):
    return tuple(sum(row[i] for row in values)/len(values) for i in range(3))


def _subtract(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _length(value):
    return math.sqrt(sum(x*x for x in value))


def _summary(values):
    return {"min": min(values), "mean": sum(values)/len(values), "max": max(values)}


def _window(frames, skeleton):
    sdk = tuple(_mean_q([f.delta_pose.sdk_global_rotation_deltas[i] for f in frames]) for i in range(24))
    canonical = tuple(_mean_q([f.canonical.global_rotations[i] for f in frames]) for i in range(24))
    locals_by_frame = [global_to_local_rotations(skeleton, f.canonical.global_rotations) for f in frames]
    local = tuple(_mean_q([row[i] for row in locals_by_frame]) for i in range(24))
    root = _mean_v([f.delta_pose.root_translation for f in frames])
    noise_m = max(_length(_subtract(f.delta_pose.root_translation, root)) for f in frames)
    noise_deg = tuple(max(rotation_distance(canonical[i], f.canonical.global_rotations[i]) for f in frames) for i in range(24))
    local_noise_deg = tuple(max(rotation_distance(local[i], row[i]) for row in locals_by_frame) for i in range(24))
    anchors = {}
    for role in SEMANTIC_TRACKER_ROLES:
        values = [next(a for a in f.anchors if a.role == role) for f in frames]
        anchors[role.value] = (_mean_v([a.position for a in values]), _mean_q([a.rotation for a in values]))
    pairs = {}
    for first, second in _PAIRS:
        i, j = REBOCAP_24_JOINT_NAMES.index(first), REBOCAP_24_JOINT_NAMES.index(second)
        pairs[first+"/"+second] = _summary([rotation_distance(f.canonical.global_rotations[i], f.canonical.global_rotations[j]) for f in frames])
    return dict(sdk=sdk, canonical=canonical, local=local, root=root, noise_m=noise_m,
                noise_deg=noise_deg, local_noise_deg=local_noise_deg, anchors=anchors, pairs=pairs)


def analyze_cue(cue: str, baseline: Sequence[MotionFrame], held: Sequence[MotionFrame],
                returned: Sequence[MotionFrame], source_bind: SkeletonDefinition) -> dict:
    """Analyze exact 60/20/20 windows. Returned dict contains aggregates only.

    Unknown sign is reported, not rewritten to the expected Unity convention.
    A detectable opposite-side response fails that named joint identification;
    small/noisy/non-returning or mixed-axis observations remain UNVERIFIED.
    """
    if cue not in CUES:
        raise ValueError("unknown cue")
    validate_rebocap24_skeleton(source_bind)
    counts = [len(baseline), len(held), len(returned)]
    if any(n > maximum for n, maximum in zip(counts, (60, 20, 20))):
        raise ValueError("RAM window exceeds fixed bound")
    result = {"schema": "reboretarget.phase2f-a.cue.v1", "cue": cue,
              "counts": dict(zip(("baseline", "held", "returned"), counts)),
              "result": "INCOMPLETE", "confidence": "UNVERIFIED"}
    if counts != [60, 20, 20]:
        return result
    b, h, r = (_window(window, source_bind) for window in (baseline, held, returned))
    floor_m = max(0.02, 3*b["noise_m"])
    delta = _subtract(h["root"], b["root"])
    back = _length(_subtract(r["root"], b["root"]))
    dominant = max(range(3), key=lambda i: abs(delta[i]))
    others = _length(tuple(delta[i] for i in range(3) if i != dominant))
    magnitude = abs(delta[dominant])
    position_return = back <= max(floor_m, magnitude*0.35)
    joints = {}
    invariant_error = 0.0
    for i, name in enumerate(REBOCAP_24_JOINT_NAMES):
        sdk_change = relative_rotation(b["sdk"][i], h["sdk"][i])
        canonical_change = relative_rotation(b["canonical"][i], h["canonical"][i])
        error = rotation_distance(sdk_change, canonical_change)
        invariant_error = max(invariant_error, error)
        change = axis_angle(b["canonical"][i], h["canonical"][i])
        joints[name] = dict(global_change=change,
            sdk_global_change=axis_angle(b["sdk"][i], h["sdk"][i]),
            local_change=axis_angle(b["local"][i], h["local"][i]),
            baseline_noise_deg=b["noise_deg"][i], local_baseline_noise_deg=b["local_noise_deg"][i],
            threshold_deg=max(3., 3*b["noise_deg"][i]),
            local_threshold_deg=max(3., 3*b["local_noise_deg"][i]),
            return_deg=rotation_distance(b["canonical"][i], r["canonical"][i]),
            local_return_deg=rotation_distance(b["local"][i], r["local"][i]),
            held_noise_deg=h["noise_deg"][i], local_held_noise_deg=h["local_noise_deg"][i],
            adapter_motion_error_deg=error)
    bind_globals = source_bind_global_rotations(source_bind)
    composition_error = max(rotation_distance(
        quaternion_multiply(f.delta_pose.sdk_global_rotation_deltas[i], bind_globals[i]),
        f.canonical.global_rotations[i]) for window in (baseline, held, returned)
        for f in window for i in range(24))
    root_error = max(_length(_subtract(f.delta_pose.root_translation, f.canonical.root_translation))
                     for window in (baseline, held, returned) for f in window)
    result.update(translation=dict(delta_xyz_m=list(delta), threshold_m=floor_m,
        baseline_noise_m=b["noise_m"], dominant_axis="XYZ"[dominant],
        sign=(1 if delta[dominant] > 0 else -1) if magnitude > floor_m else 0,
        magnitude_m=magnitude, cross_axis_m=others,
        cross_axis_ratio=others/magnitude if magnitude else None,
        return_distance_m=back, returned=position_return), joints=joints,
        pair_global_distance_deg={"baseline": b["pairs"], "held": h["pairs"]},
        adapter=dict(max_motion_error_deg=invariant_error, max_composition_error_deg=composition_error,
                     root_error_m=root_error,
                     result="PASS" if max(invariant_error, composition_error) <= .0001 and root_error <= 1e-9 else "FAIL"),
        anchors={role: dict(delta_xyz_m=list(_subtract(h["anchors"][role][0], value[0])),
                           rotation_change_deg=rotation_distance(value[1], h["anchors"][role][1]))
                 for role, value in b["anchors"].items()})
    result["result"] = "UNVERIFIED"
    if cue in ("right", "forward", "crouch"):
        detectable = (magnitude > floor_m and magnitude >= 2*others and position_return
                      and h["noise_m"] <= max(floor_m, magnitude*.35))
        # Do not claim translation mapping if body yaw dominates the trial.
        if cue != "crouch":
            detectable = detectable and joints["Pelvis"]["global_change"]["angle_deg"] <= 10
        if detectable:
            result["result"] = "PASS"
            expected_axis, expected_sign = {"right": ("X",1), "forward": ("Z",1), "crouch": ("Y",-1)}[cue]
            if result["translation"]["dominant_axis"] != expected_axis or result["translation"]["sign"] != expected_sign:
                result["result"] = "FAIL"
    elif cue.startswith("yaw_"):
        pelvis = joints["Pelvis"]
        relative = relative_rotation(b["canonical"][0], h["canonical"][0])
        forward = rotate_vector(relative, (0., 0., 1.))
        yaw = math.degrees(math.atan2(forward[0], forward[2]))
        result["yaw"] = dict(signed_deg=yaw, forward_xyz=list(forward),
                             sign=1 if yaw > 0 else -1 if yaw < 0 else 0)
        axis = pelvis["global_change"]["axis_xyz"]
        if (abs(yaw) > pelvis["threshold_deg"] and abs(axis[1]) >= 2*math.hypot(axis[0], axis[2])
                and pelvis["held_noise_deg"] <= max(pelvis["threshold_deg"], abs(yaw)*.35)
                and pelvis["return_deg"] <= max(pelvis["threshold_deg"], abs(yaw)*.35)):
            result["result"] = "PASS"
            if (yaw < 0) != (cue == "yaw_left"):
                result["result"] = "FAIL"
    else:
        side = "L" if cue.startswith("left_") else "R"
        other = "R" if side == "L" else "L"
        names = ("Knee",) if cue.endswith("knee") else ("Collar", "Shoulder", "Elbow")
        field = "local_change" if cue.endswith("knee") else "global_change"
        threshold_field = "local_threshold_deg" if cue.endswith("knee") else "threshold_deg"
        return_field = "local_return_deg" if cue.endswith("knee") else "return_deg"
        noise_field = "local_held_noise_deg" if cue.endswith("knee") else "held_noise_deg"
        selected = max(names, key=lambda name: joints[side+"_"+name][field]["angle_deg"])
        active = joints[side+"_"+selected]
        amount = active[field]["angle_deg"]
        opposite_joint = max((joints[other+"_"+name] for name in names),
                             key=lambda joint: joint[field]["angle_deg"])
        opposite = opposite_joint[field]["angle_deg"]
        result["side_response"] = dict(joint=side+"_"+selected, angle_deg=amount,
                                        opposite_max_deg=opposite, local=field=="local_change")
        if amount > active[threshold_field] and amount >= 2*opposite:
            if (active[return_field] <= max(active[threshold_field], amount*.35)
                    and active[noise_field] <= max(active[threshold_field], amount*.35)):
                result["result"] = "PASS"
        elif (opposite > max(opposite_joint[threshold_field], 2*amount)
              and opposite_joint[return_field] <= max(opposite_joint[threshold_field], opposite*.35)
              and opposite_joint[noise_field] <= max(opposite_joint[threshold_field], opposite*.35)):
            result["result"] = "FAIL"
    if result["adapter"]["result"] == "FAIL":
        result["result"] = "FAIL"
    if result["result"] == "PASS":
        result["confidence"] = "PROBABLE"
    return result


def clean_cue_result(data: dict) -> dict:
    """Strict finite aggregate IPC allowlist; rejects extra/free-form fields.

    This does not establish cue truth. It only ensures that a child cannot
    place raw frames, identifying strings, or unbounded structures in this
    result surface. Raises ValueError without echoing rejected content.
    """
    number = "number"
    vector = [number, number, number]
    angle = {"angle_deg": number, "axis_xyz": vector}
    summary = {key: number for key in ("min", "mean", "max")}
    joint_schema = dict(global_change=angle, sdk_global_change=angle, local_change=angle,
        baseline_noise_deg=number, local_baseline_noise_deg=number, threshold_deg=number,
        local_threshold_deg=number, return_deg=number, local_return_deg=number,
        held_noise_deg=number, local_held_noise_deg=number, adapter_motion_error_deg=number)
    schema = {
        "schema": ("reboretarget.phase2f-a.cue.v1",), "cue": CUES,
        "counts": {key: "count" for key in ("baseline", "held", "returned")},
        "result": ("PASS", "FAIL", "UNVERIFIED", "INCOMPLETE"),
        "confidence": ("PROBABLE", "UNVERIFIED"),
    }
    if not isinstance(data, dict) or data.get("cue") not in CUES:
        raise ValueError("invalid cue aggregate")
    if data.get("result") != "INCOMPLETE":
        schema.update(
            translation=dict(delta_xyz_m=vector, threshold_m=number, baseline_noise_m=number,
                dominant_axis=("X", "Y", "Z"), sign="sign", magnitude_m=number,
                cross_axis_m=number, cross_axis_ratio="optional_number",
                return_distance_m=number, returned="bool"),
            joints={name: joint_schema for name in REBOCAP_24_JOINT_NAMES},
            pair_global_distance_deg={window: {a+"/"+b: summary for a,b in _PAIRS}
                                      for window in ("baseline", "held")},
            adapter=dict(max_motion_error_deg=number,max_composition_error_deg=number,
                         root_error_m=number,result=("PASS","FAIL")),
            anchors={role.value: dict(delta_xyz_m=vector,rotation_change_deg=number)
                     for role in SEMANTIC_TRACKER_ROLES})
        if data["cue"].startswith("yaw_"):
            schema["yaw"] = dict(signed_deg=number,forward_xyz=vector,sign="sign")
        elif data["cue"] not in ("right","forward","crouch"):
            schema["side_response"] = dict(joint=REBOCAP_24_JOINT_NAMES,angle_deg=number,
                                            opposite_max_deg=number,local="bool")

    def clean(value, expected):
        if isinstance(expected, dict):
            if not isinstance(value, dict) or value.keys() != expected.keys():
                raise ValueError("invalid aggregate fields")
            return {key: clean(value[key], kind) for key, kind in expected.items()}
        if isinstance(expected, list):
            if not isinstance(value, (list, tuple)) or len(value) != len(expected):
                raise ValueError("invalid aggregate vector")
            return [clean(v, kind) for v, kind in zip(value, expected)]
        if isinstance(expected, tuple):
            if not isinstance(value, str) or value not in expected:
                raise ValueError("invalid aggregate enumeration")
            return value
        if expected == "bool":
            if type(value) is not bool:
                raise ValueError("invalid aggregate boolean")
            return value
        if expected == "optional_number" and value is None:
            return None
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("invalid aggregate number")
        if expected == "count" and (type(value) is not int or not 0 <= value <= 60):
            raise ValueError("invalid aggregate count")
        if expected == "sign" and (type(value) is not int or value not in (-1,0,1)):
            raise ValueError("invalid aggregate sign")
        return value

    cleaned = clean(data, schema)
    counts = cleaned["counts"]
    if counts["held"] > 20 or counts["returned"] > 20:
        raise ValueError("aggregate count exceeds window")
    if cleaned["result"] != "INCOMPLETE" and counts != dict(baseline=60,held=20,returned=20):
        raise ValueError("completed aggregate requires full windows")
    return cleaned
