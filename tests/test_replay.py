"""Phase 2B tests for confirmed hierarchy and synthetic sequence replay."""

from __future__ import annotations

from dataclasses import replace
import math
import unittest

from reboretarget import (
    REBOCAP_24_HIERARCHY_EVIDENCE,
    REBOCAP_24_JOINT_NAMES,
    REBOCAP_24_PARENT_INDICES,
    REBOCAP_24_PARENT_NAMES,
    REBOCAP_HIERARCHY_SOURCE_REFERENCES,
    Quaternion,
    SkeletonDefinition,
    SourcePose,
    leg_lengths_from_controls,
    quaternion_from_axis_angle,
    quaternion_inverse,
    quaternion_multiply,
    quaternion_rotation_angle_degrees,
    quaternions_equivalent,
    retarget_sequence,
    validate_rebocap24_skeleton,
)
from tests.synthetic_fixtures import (
    LEG_BEND_FRAME_DEGREES,
    ROOT_TRANSLATION_FRAMES,
    UPPER_BODY_FRAME_DEGREES,
    pose_from_local_rotations,
    synthetic_human_skeleton,
    synthetic_leg_bend_sequence,
    synthetic_root_translation_sequence,
    synthetic_upper_body_sequence,
)


POSITION_TOLERANCE_METRES = 1e-9
ROTATION_TOLERANCE = 1e-9
ANGLE_TOLERANCE_DEGREES = 1e-7
CONTINUITY_POSITION_LIMIT_METRES = 0.18


def vector_distance(left, right):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def rotation_distance_degrees(left, right):
    relative = quaternion_multiply(quaternion_inverse(left), right)
    return quaternion_rotation_angle_degrees(relative)


class NumericAssertions(unittest.TestCase):
    def assertVectorAlmostEqual(
        self, actual, expected, tolerance=POSITION_TOLERANCE_METRES
    ):
        self.assertEqual(len(actual), 3)
        self.assertEqual(len(expected), 3)
        for component, wanted in zip(actual, expected):
            self.assertAlmostEqual(component, wanted, delta=tolerance)

    def assertRotationEquivalent(self, actual, expected):
        self.assertTrue(
            quaternions_equivalent(actual, expected, tolerance=ROTATION_TOLERANCE),
            msg=f"rotations differ: {actual!r} != {expected!r}",
        )


class ConfirmedHierarchyTests(NumericAssertions):
    def test_all_24_parent_relations_match_the_official_array(self):
        expected_indices = (
            -1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8,
            9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21,
        )
        self.assertEqual(REBOCAP_24_PARENT_INDICES, expected_indices)
        expected_names = tuple(
            None if index < 0 else REBOCAP_24_JOINT_NAMES[index]
            for index in expected_indices
        )
        self.assertEqual(REBOCAP_24_PARENT_NAMES, expected_names)
        validate_rebocap24_skeleton(synthetic_human_skeleton())

    def test_every_relation_is_confirmed_by_both_official_code_sources(self):
        self.assertEqual(len(REBOCAP_24_HIERARCHY_EVIDENCE), 24)
        for joint_index, evidence in enumerate(REBOCAP_24_HIERARCHY_EVIDENCE):
            self.assertEqual(evidence.joint, REBOCAP_24_JOINT_NAMES[joint_index])
            self.assertEqual(evidence.parent_index, REBOCAP_24_PARENT_INDICES[joint_index])
            self.assertEqual(evidence.parent, REBOCAP_24_PARENT_NAMES[joint_index])
            self.assertEqual(evidence.status, "CONFIRMED")
            self.assertIn("REBOCAP_UNITY_V4", evidence.source_reference_ids)
            self.assertIn("REBOCAP_UE_V2", evidence.source_reference_ids)

    def test_official_archive_references_have_the_verified_sha256(self):
        references = {
            reference.reference_id: reference
            for reference in REBOCAP_HIERARCHY_SOURCE_REFERENCES
        }
        self.assertEqual(
            references["REBOCAP_UNITY_V4"].sha256,
            "E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF",
        )
        self.assertEqual(
            references["REBOCAP_UE_V2"].sha256,
            "AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53",
        )
        self.assertIsNone(references["REBOCAP_SDK_DOCS"].sha256)

    def test_validator_rejects_a_wrong_but_topological_parent(self):
        skeleton = synthetic_human_skeleton()
        joints = list(skeleton.joints)
        hand_index = skeleton.index("L_Hand")
        joints[hand_index] = replace(joints[hand_index], parent="L_Elbow")
        wrong = SkeletonDefinition(tuple(joints))
        with self.assertRaisesRegex(ValueError, "parent hierarchy"):
            validate_rebocap24_skeleton(wrong)


class LowerBodyReplayTests(NumericAssertions):
    def setUp(self):
        self.source = synthetic_human_skeleton(upper_leg=0.43, lower_leg=0.43)
        self.sequence = synthetic_leg_bend_sequence(self.source)

    def test_seven_frame_straight_to_bend_is_continuous(self):
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        results = retarget_sequence(self.sequence, self.source, target)
        self.assertEqual(len(results), 7)

        for previous, current in zip(results, results[1:]):
            self.assertAlmostEqual(
                rotation_distance_degrees(
                    previous.local_rotation("L_Hip"),
                    current.local_rotation("L_Hip"),
                ),
                5.0,
                delta=ANGLE_TOLERANCE_DEGREES,
            )
            self.assertAlmostEqual(
                rotation_distance_degrees(
                    previous.local_rotation("L_Knee"),
                    current.local_rotation("L_Knee"),
                ),
                10.0,
                delta=ANGLE_TOLERANCE_DEGREES,
            )
            self.assertLessEqual(
                vector_distance(
                    previous.transform("L_Ankle").position,
                    current.transform("L_Ankle").position,
                ),
                CONTINUITY_POSITION_LIMIT_METRES,
            )

        for pose, (hip_degrees, knee_degrees) in zip(
            results, LEG_BEND_FRAME_DEGREES
        ):
            hip_radians = math.radians(hip_degrees)
            combined_radians = math.radians(hip_degrees + knee_degrees)
            expected_knee = (
                -0.1,
                1.0 - 0.52 * math.cos(hip_radians),
                -0.52 * math.sin(hip_radians),
            )
            expected_ankle = (
                expected_knee[0],
                expected_knee[1] - 0.50 * math.cos(combined_radians),
                expected_knee[2] - 0.50 * math.sin(combined_radians),
            )
            self.assertVectorAlmostEqual(
                pose.transform("L_Knee").position, expected_knee
            )
            self.assertVectorAlmostEqual(
                pose.transform("L_Ankle").position, expected_ankle
            )

    def test_long_and_short_targets_keep_the_same_joint_rotations(self):
        long_target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        short_target = synthetic_human_skeleton(upper_leg=0.36, lower_leg=0.34)
        long_results = retarget_sequence(self.sequence, self.source, long_target)
        short_results = retarget_sequence(self.sequence, self.source, short_target)

        for long_pose, short_pose in zip(long_results, short_results):
            for name in ("L_Hip", "L_Knee", "R_Hip", "R_Knee"):
                self.assertRotationEquivalent(
                    long_pose.local_rotation(name), short_pose.local_rotation(name)
                )
            self.assertAlmostEqual(
                vector_distance(
                    long_pose.transform("L_Hip").position,
                    long_pose.transform("L_Knee").position,
                ),
                0.52,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                vector_distance(
                    short_pose.transform("L_Hip").position,
                    short_pose.transform("L_Knee").position,
                ),
                0.36,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                vector_distance(
                    long_pose.transform("L_Knee").position,
                    long_pose.transform("L_Ankle").position,
                ),
                0.50,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                vector_distance(
                    short_pose.transform("L_Knee").position,
                    short_pose.transform("L_Ankle").position,
                ),
                0.34,
                delta=POSITION_TOLERANCE_METRES,
            )

    def test_leg_length_control_applies_to_every_frame(self):
        upper, lower = leg_lengths_from_controls(0.43, 0.43, leg_length=1.10)
        target = synthetic_human_skeleton(upper_leg=upper, lower_leg=lower)
        results = retarget_sequence(self.sequence, self.source, target)
        for pose in results:
            hip_to_knee = vector_distance(
                pose.transform("L_Hip").position, pose.transform("L_Knee").position
            )
            knee_to_ankle = vector_distance(
                pose.transform("L_Knee").position, pose.transform("L_Ankle").position
            )
            self.assertAlmostEqual(hip_to_knee, 0.473, delta=1e-9)
            self.assertAlmostEqual(knee_to_ankle, 0.473, delta=1e-9)
            self.assertAlmostEqual(hip_to_knee + knee_to_ankle, 0.946, delta=1e-9)

    def test_balance_preserves_total_and_moves_straight_knee_only(self):
        neutral = synthetic_human_skeleton(upper_leg=0.43, lower_leg=0.43)
        balanced_lengths = leg_lengths_from_controls(
            0.43, 0.43, thigh_calf_balance=0.10
        )
        balanced = synthetic_human_skeleton(
            upper_leg=balanced_lengths[0], lower_leg=balanced_lengths[1]
        )
        neutral_results = retarget_sequence(self.sequence, self.source, neutral)
        balanced_results = retarget_sequence(self.sequence, self.source, balanced)

        for neutral_pose, balanced_pose in zip(neutral_results, balanced_results):
            self.assertRotationEquivalent(
                neutral_pose.local_rotation("L_Knee"),
                balanced_pose.local_rotation("L_Knee"),
            )
            for pose in (neutral_pose, balanced_pose):
                total = vector_distance(
                    pose.transform("L_Hip").position,
                    pose.transform("L_Knee").position,
                ) + vector_distance(
                    pose.transform("L_Knee").position,
                    pose.transform("L_Ankle").position,
                )
                self.assertAlmostEqual(total, 0.86, delta=POSITION_TOLERANCE_METRES)

        neutral_straight = neutral_results[0]
        balanced_straight = balanced_results[0]
        self.assertVectorAlmostEqual(
            neutral_straight.transform("L_Ankle").position,
            balanced_straight.transform("L_Ankle").position,
        )
        self.assertAlmostEqual(
            neutral_straight.transform("L_Knee").position[1]
            - balanced_straight.transform("L_Knee").position[1],
            0.086,
            delta=POSITION_TOLERANCE_METRES,
        )

    def test_every_replay_frame_remains_left_right_mirrored(self):
        target = synthetic_human_skeleton(upper_leg=0.50, lower_leg=0.48)
        results = retarget_sequence(self.sequence, self.source, target)
        for pose in results:
            for left_name, right_name in (
                ("L_Hip", "R_Hip"),
                ("L_Knee", "R_Knee"),
                ("L_Ankle", "R_Ankle"),
                ("L_Foot", "R_Foot"),
            ):
                left = pose.transform(left_name)
                right = pose.transform(right_name)
                self.assertAlmostEqual(left.position[0], -right.position[0], delta=1e-9)
                self.assertAlmostEqual(left.position[1], right.position[1], delta=1e-9)
                self.assertAlmostEqual(left.position[2], right.position[2], delta=1e-9)
                self.assertRotationEquivalent(left.rotation, right.rotation)


class RootAndQuaternionContinuityTests(NumericAssertions):
    def test_root_xyz_translation_moves_every_joint_by_the_exact_delta(self):
        skeleton = synthetic_human_skeleton()
        sequence = synthetic_root_translation_sequence(skeleton)
        results = retarget_sequence(sequence, skeleton, skeleton)
        base = results[0]
        base_translation = ROOT_TRANSLATION_FRAMES[0]

        for translation, pose in zip(ROOT_TRANSLATION_FRAMES, results):
            delta = tuple(a - b for a, b in zip(translation, base_translation))
            for name in skeleton.joint_names:
                expected = tuple(
                    component + shift
                    for component, shift in zip(base.transform(name).position, delta)
                )
                self.assertVectorAlmostEqual(pose.transform(name).position, expected)
                self.assertRotationEquivalent(
                    pose.transform(name).rotation, base.transform(name).rotation
                )

    def test_q_sign_flip_and_179_to_181_boundary_have_no_false_jump(self):
        skeleton = synthetic_human_skeleton()

        def signed_pose(angle, negate):
            base = pose_from_local_rotations(
                skeleton,
                {"L_Knee": quaternion_from_axis_angle((1.0, 0.0, 0.0), angle)},
            )
            rotations = tuple(
                rotation.negated() if negate else rotation
                for rotation in base.global_rotations
            )
            return SourcePose(base.root_translation, rotations)

        sequence = (
            signed_pose(179.0, False),
            signed_pose(179.0, True),
            signed_pose(181.0, True),
            signed_pose(181.0, False),
        )
        results = retarget_sequence(sequence, skeleton, skeleton)
        distances = [
            rotation_distance_degrees(
                previous.local_rotation("L_Knee"), current.local_rotation("L_Knee")
            )
            for previous, current in zip(results, results[1:])
        ]
        for actual, expected in zip(distances, (0.0, 2.0, 0.0)):
            self.assertAlmostEqual(actual, expected, delta=ANGLE_TOLERANCE_DEGREES)

    def test_sequence_replay_is_deterministic_and_does_not_mutate_input(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        sequence = synthetic_leg_bend_sequence(source)
        before = sequence
        self.assertEqual(
            retarget_sequence(sequence, source, target),
            retarget_sequence(sequence, source, target),
        )
        self.assertEqual(sequence, before)


class UpperBodyReplayTests(NumericAssertions):
    def test_five_frame_upper_body_chain_uses_the_same_fk_core(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(shoulder_width_scale=1.10)
        sequence = synthetic_upper_body_sequence(source)
        results = retarget_sequence(sequence, source, target)
        self.assertEqual(len(results), 5)

        for previous, current in zip(results, results[1:]):
            expected_steps = {
                "Spine3": 5.0,
                "L_Collar": 2.5,
                "L_Shoulder": 7.5,
                "L_Elbow": 10.0,
            }
            for name, expected in expected_steps.items():
                self.assertAlmostEqual(
                    rotation_distance_degrees(
                        previous.local_rotation(name), current.local_rotation(name)
                    ),
                    expected,
                    delta=ANGLE_TOLERANCE_DEGREES,
                )

        spine, collar, shoulder, elbow = UPPER_BODY_FRAME_DEGREES[-1]
        expected = Quaternion.identity()
        for rotation in (
            quaternion_from_axis_angle((0.0, 1.0, 0.0), spine),
            quaternion_from_axis_angle((0.0, 0.0, 1.0), collar),
            quaternion_from_axis_angle((0.0, 1.0, 0.0), shoulder),
            quaternion_from_axis_angle((0.0, 0.0, 1.0), elbow),
        ):
            expected = quaternion_multiply(expected, rotation)
        self.assertRotationEquivalent(results[-1].transform("L_Elbow").rotation, expected)

    def test_fixture_only_shoulder_width_scales_shoulder_span_not_arm_lengths(self):
        source = synthetic_human_skeleton()
        base_target = synthetic_human_skeleton(shoulder_width_scale=1.0)
        wide_target = synthetic_human_skeleton(shoulder_width_scale=1.10)
        source_pose = synthetic_upper_body_sequence(source)[0]
        base, wide = (
            retarget_sequence((source_pose,), source, target)[0]
            for target in (base_target, wide_target)
        )

        base_span = (
            base.transform("R_Shoulder").position[0]
            - base.transform("L_Shoulder").position[0]
        )
        wide_span = (
            wide.transform("R_Shoulder").position[0]
            - wide.transform("L_Shoulder").position[0]
        )
        self.assertAlmostEqual(wide_span, base_span * 1.10, delta=1e-9)
        for pose in (base, wide):
            self.assertAlmostEqual(
                vector_distance(
                    pose.transform("L_Shoulder").position,
                    pose.transform("L_Elbow").position,
                ),
                0.28,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                vector_distance(
                    pose.transform("L_Elbow").position,
                    pose.transform("L_Wrist").position,
                ),
                0.25,
                delta=POSITION_TOLERANCE_METRES,
            )


if __name__ == "__main__":
    unittest.main()
