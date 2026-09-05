"""Combined synthetic proportions through FK, eight anchors and memory OSC only."""

import math
import unittest

from reboretarget import (
    Quaternion, SourcePose, arm_lengths_from_controls, build_osc_tracker_poses,
    build_tracker_messages, build_tracker_transforms, decode_osc_float3_message,
    encode_osc_float3_message, quaternion_from_axis_angle, quaternion_multiply,
    quaternions_equivalent, retarget_pose, synthetic_tracker_anchor_definitions,
    vrchat_euler_degrees_to_quaternion,
)
from tests.synthetic_fixtures import pose_from_local_rotations, synthetic_human_skeleton


def composite_targets():
    for scale, balance, thigh, calf, hips, shoulders in (
        (1.2, .1, .60, .36, .32, 1.4),
        (.8, -.15, .32, .48, .14, .7),
    ):
        upper, forearm = arm_lengths_from_controls(
            .28, .25, arm_length=scale, upper_arm_forearm_balance=balance)
        yield synthetic_human_skeleton(
            upper_leg=thigh, lower_leg=calf, hip_width=hips,
            shoulder_width_scale=shoulders, upper_arm=upper, forearm=forearm)


def compound_locals(amount=1.):
    # Asymmetric joints on three axes expose ordering and left/right mixups.
    return {name: quaternion_from_axis_angle(axis, angle * amount)
            for name, axis, angle in (
                ("Spine3", (0, 1, 0), 20),
                ("L_Collar", (0, 0, 1), 15), ("R_Collar", (0, 0, 1), -7),
                ("L_Shoulder", (0, 1, 0), 50), ("R_Shoulder", (1, 0, 0), 25),
                ("L_Elbow", (0, 0, 1), 70), ("R_Elbow", (0, 1, 0), -40),
                ("L_Hip", (1, 0, 0), -20), ("R_Hip", (0, 0, 1), 12),
                ("L_Knee", (1, 0, 0), 60), ("R_Knee", (1, 0, 0), 35),
            )}


class CompositeMorphologyTests(unittest.TestCase):
    def assertVector(self, actual, expected, delta=1e-9):
        self.assertEqual(len(actual), len(expected))
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want, delta=delta)

    def anchors(self, pose, source, target):
        return build_tracker_transforms(
            retarget_pose(pose, source, target), synthetic_tracker_anchor_definitions(target))

    def test_two_composite_neutral_bodies_match_independent_positions(self):
        source = synthetic_human_skeleton()
        pose = pose_from_local_rotations(source)
        # Hand-calculated from the two requested proportions, not target FK/offsets.
        expected = (
            (.16, .40, .04, .4798, .916),
            (.07, .68, .20, .2202, .564),
        )
        roles = ("Hip", "Chest", "Left Knee", "Right Knee", "Left Foot",
                 "Right Foot", "Left Upper Arm", "Right Upper Arm")
        for target, (half_hip, knee_y, foot_y, arm_x, wrist_x) in zip(composite_targets(), expected):
            with self.subTest(half_hip=half_hip):
                points = ((0., 1., .04), (0., 1.50, .04),
                          (-half_hip, knee_y, .03), (half_hip, knee_y, .03),
                          (-half_hip, foot_y, .09), (half_hip, foot_y, .09),
                          (-arm_x, 1.53, 0.), (arm_x, 1.53, 0.))
                anchors = self.anchors(pose, source, target)
                self.assertEqual(tuple(anchor.role.value for anchor in anchors), roles)
                for anchor, point in zip(anchors, points):
                    self.assertVector(anchor.position, point)
                    self.assertTrue(quaternions_equivalent(anchor.rotation, Quaternion.identity()))
                result = retarget_pose(pose, source, target)
                for side, sign in (("L", -1), ("R", 1)):
                    self.assertVector(result.transform(side + "_Wrist").position,
                                      (sign * wrist_x, 1.53, 0.))

    def test_compound_sequence_preserves_every_segment_and_authored_local_rotation(self):
        source = synthetic_human_skeleton()
        for target in composite_targets():
            for amount in (.25, 1.):
                local = compound_locals(amount)
                result = retarget_pose(pose_from_local_rotations(source, local), source, target)
                for joint in target.joints:
                    with self.subTest(arm=target.joint("L_Elbow").segment_length,
                                      amount=amount, joint=joint.name):
                        self.assertTrue(quaternions_equivalent(
                            result.local_rotation(joint.name), local.get(joint.name, Quaternion.identity())))
                        if joint.parent is not None:
                            self.assertAlmostEqual(math.dist(result.transform(joint.name).position,
                                                            result.transform(joint.parent).position),
                                                   joint.segment_length, delta=1e-9)

    def test_yaw_translation_and_quaternion_sign_survive_all_sixteen_memory_messages(self):
        source = synthetic_human_skeleton()
        pose = pose_from_local_rotations(source, compound_locals())
        yaw = quaternion_from_axis_angle((0, 1, 0), 90)
        # A +90 Y rotation maps (x,y,z) to (z,y,-x); then translate (.3,.2,-.4).
        shifted = SourcePose((.3, 1.2, -.4), tuple(
            quaternion_multiply(yaw, q).negated() if i % 2 else quaternion_multiply(yaw, q)
            for i, q in enumerate(pose.global_rotations)))
        for target in composite_targets():
            baseline = self.anchors(pose, source, target)
            transformed = self.anchors(shifted, source, target)
            messages = build_tracker_messages(build_osc_tracker_poses(transformed))
            decoded = [decode_osc_float3_message(encode_osc_float3_message(m)) for m in messages]
            self.assertEqual(len(decoded), 16)
            self.assertEqual(len({m.address for m in decoded}), 16)
            by_address = {m.address: m.values for m in decoded}
            for slot, (before, after) in enumerate(zip(baseline, transformed), 1):
                self.assertEqual(after.role, before.role)
                x, y, z = before.position
                expected_position = (z + .3, y + .2, -x - .4)
                expected_rotation = quaternion_multiply(yaw, before.rotation)
                self.assertVector(after.position, expected_position)
                self.assertTrue(quaternions_equivalent(after.rotation, expected_rotation))
                self.assertVector(by_address[f"/tracking/trackers/{slot}/position"],
                                  expected_position, delta=1e-6)
                decoded_rotation = vrchat_euler_degrees_to_quaternion(
                    by_address[f"/tracking/trackers/{slot}/rotation"])
                self.assertTrue(quaternions_equivalent(decoded_rotation, expected_rotation))
