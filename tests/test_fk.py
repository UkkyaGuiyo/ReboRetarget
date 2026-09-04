"""Numeric acceptance tests for the Phase 2A pure/offline FK PoC."""

from __future__ import annotations

import math
import unittest

from reboretarget import (
    REBOCAP_24_PARENT_NAMES,
    REBOCAP_24_JOINT_NAMES,
    JointDefinition,
    Quaternion,
    SkeletonDefinition,
    SourcePose,
    forward_kinematics,
    global_to_local_rotations,
    leg_lengths_from_controls,
    quaternion_from_axis_angle,
    quaternion_multiply,
    quaternions_equivalent,
    retarget_pose,
    rotate_vector,
    validate_rebocap24_skeleton,
)
from tests.synthetic_fixtures import (
    pose_from_local_rotations,
    synthetic_human_skeleton,
)


POSITION_TOLERANCE_METRES = 1e-9
ROTATION_TOLERANCE = 1e-9
ANGLE_TOLERANCE_DEGREES = 1e-7


class NumericAssertions(unittest.TestCase):
    def assertVectorAlmostEqual(self, actual, expected, tolerance=POSITION_TOLERANCE_METRES):
        self.assertEqual(len(actual), 3)
        self.assertEqual(len(expected), 3)
        for component, wanted in zip(actual, expected):
            self.assertAlmostEqual(component, wanted, delta=tolerance)

    def assertRotationEquivalent(self, actual, expected):
        self.assertTrue(
            quaternions_equivalent(actual, expected, tolerance=ROTATION_TOLERANCE),
            msg=f"rotations differ: {actual!r} != {expected!r}",
        )


class SkeletonAndInputContractTests(NumericAssertions):
    def test_confirmed_24_order_and_parent_hierarchy(self):
        skeleton = synthetic_human_skeleton()
        self.assertEqual(skeleton.joint_names, REBOCAP_24_JOINT_NAMES)
        self.assertEqual(
            tuple(joint.parent for joint in skeleton.joints),
            REBOCAP_24_PARENT_NAMES,
        )
        validate_rebocap24_skeleton(skeleton)

    def test_rebocap_validator_rejects_a_swapped_joint_order(self):
        skeleton = synthetic_human_skeleton()
        joints = list(skeleton.joints)
        joints[10], joints[11] = joints[11], joints[10]
        with self.assertRaisesRegex(ValueError, "joint order"):
            validate_rebocap24_skeleton(SkeletonDefinition(tuple(joints)))

    def test_rebocap_input_requires_exactly_24_wxyz_rotations(self):
        identity = (1.0, 0.0, 0.0, 0.0)
        pose = SourcePose.from_rebocap24((0.0, 1.0, 0.0), [identity] * 24)
        self.assertEqual(len(pose.global_rotations), 24)
        with self.assertRaisesRegex(ValueError, "exactly 24"):
            SourcePose.from_rebocap24((0.0, 1.0, 0.0), [identity] * 23)

    def test_segment_length_is_derived_from_rest_vector(self):
        joint = JointDefinition("Child", "Root", (0.0, -0.3, 0.4))
        self.assertAlmostEqual(joint.segment_length, 0.5, delta=1e-12)

    def test_non_topological_hierarchy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must appear before"):
            SkeletonDefinition(
                (
                    JointDefinition("Root", None, (0.0, 0.0, 0.0)),
                    JointDefinition("Grandchild", "Child", (0.0, 1.0, 0.0)),
                    JointDefinition("Child", "Root", (0.0, 1.0, 0.0)),
                )
            )


class QuaternionConventionTests(NumericAssertions):
    def test_hamilton_wxyz_active_axis_rotation(self):
        rotate_z_90 = quaternion_from_axis_angle((0.0, 0.0, 1.0), 90.0)
        self.assertVectorAlmostEqual(
            rotate_vector(rotate_z_90, (1.0, 0.0, 0.0)),
            (0.0, 1.0, 0.0),
        )

    def test_multiply_applies_right_then_left(self):
        rotate_z_90 = quaternion_from_axis_angle((0.0, 0.0, 1.0), 90.0)
        rotate_x_90 = quaternion_from_axis_angle((1.0, 0.0, 0.0), 90.0)
        x_then_z = quaternion_multiply(rotate_z_90, rotate_x_90)
        z_then_x = quaternion_multiply(rotate_x_90, rotate_z_90)
        self.assertVectorAlmostEqual(
            rotate_vector(x_then_z, (0.0, 1.0, 0.0)),
            (0.0, 0.0, 1.0),
        )
        self.assertVectorAlmostEqual(
            rotate_vector(z_then_x, (0.0, 1.0, 0.0)),
            (-1.0, 0.0, 0.0),
        )

    def test_q_and_negated_q_are_the_same_rotation(self):
        rotation = quaternion_from_axis_angle((0.3, 0.5, 0.8), 73.0)
        self.assertTrue(quaternions_equivalent(rotation, rotation.negated()))
        self.assertVectorAlmostEqual(
            rotate_vector(rotation, (0.2, -0.4, 0.7)),
            rotate_vector(rotation.negated(), (0.2, -0.4, 0.7)),
        )

    def test_retarget_is_unchanged_by_equivalent_quaternion_signs(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        knee = quaternion_from_axis_angle((1.0, 0.0, 0.0), 33.0)
        pose = pose_from_local_rotations(source, {"L_Knee": knee})
        signed_pose = SourcePose(
            pose.root_translation,
            tuple(
                rotation.negated() if index % 2 else rotation
                for index, rotation in enumerate(pose.global_rotations)
            ),
        )
        normal = retarget_pose(pose, source, target)
        signed = retarget_pose(signed_pose, source, target)
        for normal_transform, signed_transform in zip(
            normal.world_transforms, signed.world_transforms
        ):
            self.assertVectorAlmostEqual(normal_transform.position, signed_transform.position)
            self.assertRotationEquivalent(normal_transform.rotation, signed_transform.rotation)


class GlobalToLocalTests(NumericAssertions):
    def test_identity_globals_recover_identity_locals(self):
        skeleton = synthetic_human_skeleton()
        identity = Quaternion.identity()
        locals_out = global_to_local_rotations(skeleton, (identity,) * 24)
        for local in locals_out:
            self.assertRotationEquivalent(local, identity)

    def test_parent_child_compound_rotation_is_recovered(self):
        skeleton = synthetic_human_skeleton()
        parent_local = quaternion_from_axis_angle((0.0, 0.0, 1.0), 40.0)
        child_local = quaternion_from_axis_angle((1.0, 0.0, 0.0), 35.0)
        pose = pose_from_local_rotations(
            skeleton,
            {"L_Hip": parent_local, "L_Knee": child_local},
        )
        locals_out = global_to_local_rotations(skeleton, pose.global_rotations)
        self.assertRotationEquivalent(locals_out[skeleton.index("L_Hip")], parent_local)
        self.assertRotationEquivalent(locals_out[skeleton.index("L_Knee")], child_local)

    def test_nonidentity_source_and_target_rest_round_trip(self):
        source_root_rest = quaternion_from_axis_angle((0.0, 1.0, 0.0), 10.0)
        source_child_rest = quaternion_from_axis_angle((1.0, 0.0, 0.0), 20.0)
        target_root_rest = quaternion_from_axis_angle((0.0, 0.0, 1.0), -15.0)
        target_child_rest = quaternion_from_axis_angle((0.0, 1.0, 0.0), 30.0)
        source = SkeletonDefinition(
            (
                JointDefinition("Root", None, (0.0, 0.0, 0.0), source_root_rest),
                JointDefinition("Child", "Root", (0.0, -0.4, 0.0), source_child_rest),
            )
        )
        target = SkeletonDefinition(
            (
                JointDefinition("Root", None, (0.0, 0.0, 0.0), target_root_rest),
                JointDefinition("Child", "Root", (0.0, -0.7, 0.0), target_child_rest),
            )
        )
        child_delta = quaternion_from_axis_angle((0.0, 0.0, 1.0), 25.0)
        source_child_local = quaternion_multiply(source_child_rest, child_delta)
        source_child_global = quaternion_multiply(source_root_rest, source_child_local)
        pose = SourcePose((0.2, 1.1, -0.3), (source_root_rest, source_child_global))

        result = retarget_pose(pose, source, target)
        self.assertRotationEquivalent(result.local_rotation("Root"), target_root_rest)
        self.assertRotationEquivalent(
            result.local_rotation("Child"),
            quaternion_multiply(target_child_rest, child_delta),
        )
        self.assertAlmostEqual(target.joint("Child").segment_length, 0.7, delta=1e-12)


class LegForwardKinematicsTests(NumericAssertions):
    def setUp(self):
        self.source = synthetic_human_skeleton(upper_leg=0.43, lower_leg=0.43)

    def test_t_pose_and_straight_leg_use_target_rest_lengths(self):
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        pose = pose_from_local_rotations(
            self.source, root_translation=(0.2, 1.2, -0.1)
        )
        result = retarget_pose(pose, self.source, target)

        self.assertVectorAlmostEqual(result.transform("Pelvis").position, (0.2, 1.2, -0.1))
        self.assertVectorAlmostEqual(result.transform("L_Knee").position, (0.1, 0.68, -0.1))
        self.assertVectorAlmostEqual(result.transform("L_Ankle").position, (0.1, 0.18, -0.1))
        self.assertRotationEquivalent(result.local_rotation("L_Knee"), Quaternion.identity())
        self.assertAlmostEqual(
            result.diagnostic("L_Knee").local_rotation_magnitude_degrees,
            0.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )

    def test_knee_90_degrees_bends_only_target_lower_leg(self):
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        knee_90 = quaternion_from_axis_angle((1.0, 0.0, 0.0), 90.0)
        pose = pose_from_local_rotations(self.source, {"L_Knee": knee_90})
        result = retarget_pose(pose, self.source, target)

        self.assertVectorAlmostEqual(result.transform("L_Knee").position, (-0.1, 0.48, 0.0))
        self.assertVectorAlmostEqual(result.transform("L_Ankle").position, (-0.1, 0.48, -0.50))
        self.assertRotationEquivalent(result.local_rotation("L_Knee"), knee_90)

    def test_hip_30_plus_knee_45_propagates_parent_and_child(self):
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        hip_30 = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        knee_45 = quaternion_from_axis_angle((1.0, 0.0, 0.0), 45.0)
        pose = pose_from_local_rotations(
            self.source,
            {"L_Hip": hip_30, "L_Knee": knee_45},
        )
        result = retarget_pose(pose, self.source, target)

        knee_expected = (
            -0.1,
            1.0 - 0.52 * math.cos(math.radians(30.0)),
            -0.52 * math.sin(math.radians(30.0)),
        )
        ankle_expected = (
            -0.1,
            knee_expected[1] - 0.50 * math.cos(math.radians(75.0)),
            knee_expected[2] - 0.50 * math.sin(math.radians(75.0)),
        )
        self.assertVectorAlmostEqual(result.transform("L_Knee").position, knee_expected)
        self.assertVectorAlmostEqual(result.transform("L_Ankle").position, ankle_expected)
        self.assertRotationEquivalent(
            result.transform("L_Knee").rotation,
            quaternion_from_axis_angle((1.0, 0.0, 0.0), 75.0),
        )

    def test_long_and_short_targets_preserve_straight_pose(self):
        pose = pose_from_local_rotations(self.source)
        long_target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        short_target = synthetic_human_skeleton(upper_leg=0.36, lower_leg=0.34)
        long_result = retarget_pose(pose, self.source, long_target)
        short_result = retarget_pose(pose, self.source, short_target)

        self.assertAlmostEqual(
            long_result.transform("L_Hip").position[1]
            - long_result.transform("L_Ankle").position[1],
            1.02,
            delta=POSITION_TOLERANCE_METRES,
        )
        self.assertAlmostEqual(
            short_result.transform("L_Hip").position[1]
            - short_result.transform("L_Ankle").position[1],
            0.70,
            delta=POSITION_TOLERANCE_METRES,
        )
        self.assertRotationEquivalent(long_result.local_rotation("L_Knee"), Quaternion.identity())
        self.assertRotationEquivalent(short_result.local_rotation("L_Knee"), Quaternion.identity())

    def test_source_bone_length_does_not_change_a_fixed_target_result(self):
        short_source = synthetic_human_skeleton(upper_leg=0.31, lower_leg=0.29)
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        standard_result = retarget_pose(
            pose_from_local_rotations(self.source), self.source, target
        )
        short_source_result = retarget_pose(
            pose_from_local_rotations(short_source), short_source, target
        )
        for joint_name in ("L_Knee", "L_Ankle", "R_Knee", "R_Ankle"):
            self.assertVectorAlmostEqual(
                standard_result.transform(joint_name).position,
                short_source_result.transform(joint_name).position,
            )

    def test_left_right_symmetry_uses_the_same_fk_rule(self):
        target = synthetic_human_skeleton(upper_leg=0.50, lower_leg=0.48)
        hip = quaternion_from_axis_angle((1.0, 0.0, 0.0), 22.0)
        knee = quaternion_from_axis_angle((1.0, 0.0, 0.0), 37.0)
        pose = pose_from_local_rotations(
            self.source,
            {
                "L_Hip": hip,
                "R_Hip": hip,
                "L_Knee": knee,
                "R_Knee": knee,
            },
        )
        result = retarget_pose(pose, self.source, target)
        for left_name, right_name in (("L_Knee", "R_Knee"), ("L_Ankle", "R_Ankle")):
            left = result.transform(left_name)
            right = result.transform(right_name)
            self.assertAlmostEqual(left.position[0], -right.position[0], delta=POSITION_TOLERANCE_METRES)
            self.assertAlmostEqual(left.position[1], right.position[1], delta=POSITION_TOLERANCE_METRES)
            self.assertAlmostEqual(left.position[2], right.position[2], delta=POSITION_TOLERANCE_METRES)
            self.assertRotationEquivalent(left.rotation, right.rotation)

    def test_parent_world_rotation_moves_child_rest_vector(self):
        target = synthetic_human_skeleton()
        pelvis_90 = quaternion_from_axis_angle((0.0, 0.0, 1.0), 90.0)
        pose = pose_from_local_rotations(self.source, {"Pelvis": pelvis_90})
        result = retarget_pose(pose, self.source, target)
        self.assertVectorAlmostEqual(result.transform("L_Hip").position, (0.0, 0.9, 0.0))
        self.assertVectorAlmostEqual(result.transform("R_Hip").position, (0.0, 1.1, 0.0))


class InheritanceDiagnosticTests(NumericAssertions):
    def setUp(self):
        self.skeleton = synthetic_human_skeleton()

    def test_complete_parent_rotation_inheritance_is_identity_local(self):
        hip = quaternion_from_axis_angle((0.0, 0.0, 1.0), 28.0)
        globals_out = list(pose_from_local_rotations(self.skeleton).global_rotations)
        globals_out[self.skeleton.index("L_Hip")] = hip
        globals_out[self.skeleton.index("L_Knee")] = hip
        pose = SourcePose((0.0, 1.0, 0.0), tuple(globals_out))
        result = retarget_pose(pose, self.skeleton, self.skeleton)
        diagnostic = result.diagnostic("L_Knee")
        self.assertAlmostEqual(
            diagnostic.local_rotation_magnitude_degrees,
            0.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )

    def test_independent_child_rotation_is_measured(self):
        hip = quaternion_from_axis_angle((0.0, 1.0, 0.0), 20.0)
        child = quaternion_from_axis_angle((1.0, 0.0, 0.0), 15.0)
        pose = pose_from_local_rotations(
            self.skeleton, {"L_Hip": hip, "L_Knee": child}
        )
        result = retarget_pose(pose, self.skeleton, self.skeleton)
        diagnostic = result.diagnostic("L_Knee")
        self.assertAlmostEqual(
            diagnostic.local_rotation_magnitude_degrees,
            15.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )

    def test_small_independent_rotation_is_preserved_as_a_number(self):
        tiny = quaternion_from_axis_angle((1.0, 0.0, 0.0), 0.05)
        pose = pose_from_local_rotations(self.skeleton, {"L_Knee": tiny})
        result = retarget_pose(pose, self.skeleton, self.skeleton)
        diagnostic = result.diagnostic("L_Knee")
        self.assertAlmostEqual(
            diagnostic.local_rotation_magnitude_degrees,
            0.05,
            delta=ANGLE_TOLERANCE_DEGREES,
        )

    def test_left_right_asymmetry_remains_visible(self):
        right_knee = quaternion_from_axis_angle((0.0, 0.0, 1.0), 12.0)
        pose = pose_from_local_rotations(self.skeleton, {"R_Knee": right_knee})
        result = retarget_pose(pose, self.skeleton, self.skeleton)
        self.assertAlmostEqual(
            result.diagnostic("L_Knee").local_rotation_magnitude_degrees,
            0.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )
        self.assertAlmostEqual(
            result.diagnostic("R_Knee").local_rotation_magnitude_degrees,
            12.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )


class UpperBodyExtensionTests(NumericAssertions):
    def test_spine_shoulder_motion_and_elbow_inheritance_use_the_same_core(self):
        skeleton = synthetic_human_skeleton()
        spine = quaternion_from_axis_angle((0.0, 1.0, 0.0), 20.0)
        shoulder = quaternion_from_axis_angle((0.0, 0.0, 1.0), 30.0)
        pose = pose_from_local_rotations(
            skeleton,
            {"Spine3": spine, "L_Shoulder": shoulder},
        )
        result = retarget_pose(pose, skeleton, skeleton)
        expected_shoulder_world = quaternion_multiply(spine, shoulder)

        self.assertRotationEquivalent(
            result.transform("L_Shoulder").rotation, expected_shoulder_world
        )
        self.assertRotationEquivalent(
            result.transform("L_Elbow").rotation, expected_shoulder_world
        )
        self.assertAlmostEqual(
            result.diagnostic("L_Shoulder").local_rotation_magnitude_degrees,
            30.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )
        self.assertAlmostEqual(
            result.diagnostic("L_Elbow").local_rotation_magnitude_degrees,
            0.0,
            delta=ANGLE_TOLERANCE_DEGREES,
        )


class UserControlTests(NumericAssertions):
    def test_leg_length_110_makes_total_exactly_ten_percent_longer(self):
        upper, lower = leg_lengths_from_controls(0.43, 0.43, leg_length=1.10)
        self.assertAlmostEqual(upper + lower, 0.86 * 1.10, delta=1e-12)
        self.assertAlmostEqual(upper, lower, delta=1e-12)

    def test_balance_moves_knee_without_changing_total_leg_length(self):
        neutral = leg_lengths_from_controls(0.43, 0.43)
        thigh_heavy = leg_lengths_from_controls(
            0.43, 0.43, thigh_calf_balance=0.10
        )
        self.assertAlmostEqual(sum(neutral), sum(thigh_heavy), delta=1e-12)
        self.assertAlmostEqual(thigh_heavy[0] - neutral[0], 0.086, delta=1e-12)
        self.assertAlmostEqual(neutral[1] - thigh_heavy[1], 0.086, delta=1e-12)

    def test_invalid_balance_cannot_create_zero_or_negative_segment(self):
        with self.assertRaisesRegex(ValueError, "both segments positive"):
            leg_lengths_from_controls(0.43, 0.43, thigh_calf_balance=0.50)


class PurityAndValidationTests(NumericAssertions):
    def test_same_input_produces_equal_output_without_mutation(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        pose = pose_from_local_rotations(
            source,
            {"L_Knee": quaternion_from_axis_angle((1.0, 0.0, 0.0), 20.0)},
        )
        before = pose
        first = retarget_pose(pose, source, target)
        second = retarget_pose(pose, source, target)
        self.assertEqual(first, second)
        self.assertEqual(pose, before)

    def test_fk_rejects_rotation_count_mismatch(self):
        skeleton = synthetic_human_skeleton()
        with self.assertRaisesRegex(ValueError, "must match skeleton"):
            forward_kinematics(skeleton, (0.0, 0.0, 0.0), [Quaternion.identity()])

    def test_retarget_rejects_nonfinite_pose_values(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            SourcePose((math.nan, 0.0, 0.0), (Quaternion.identity(),))


if __name__ == "__main__":
    unittest.main()
