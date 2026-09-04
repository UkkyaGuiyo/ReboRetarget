"""Phase 2C tests for pure semantic tracker-anchor transforms."""

from __future__ import annotations

from dataclasses import replace
import unittest

from reboretarget import (
    Quaternion,
    ReboCapDeltaPose,
    SemanticTrackerRole,
    adapt_rebocap_delta_pose,
    build_tracker_transforms,
    quaternion_from_axis_angle,
    quaternion_inverse,
    quaternion_multiply,
    quaternions_equivalent,
    retarget_pose,
    rotate_vector,
    source_bind_global_rotations,
    synthetic_tracker_anchor_definitions,
)
from tests.synthetic_fixtures import (
    pose_from_local_rotations,
    synthetic_human_skeleton,
    synthetic_root_translation_sequence,
)


POSITION_TOLERANCE_METRES = 1e-9
ROTATION_TOLERANCE = 1e-9


class NumericAssertions(unittest.TestCase):
    def assertVectorAlmostEqual(self, actual, expected):
        self.assertEqual(len(actual), 3)
        self.assertEqual(len(expected), 3)
        for component, wanted in zip(actual, expected):
            self.assertAlmostEqual(
                component, wanted, delta=POSITION_TOLERANCE_METRES
            )

    def assertRotationEquivalent(self, actual, expected):
        self.assertTrue(
            quaternions_equivalent(actual, expected, tolerance=ROTATION_TOLERANCE),
            msg=f"rotations differ: {actual!r} != {expected!r}",
        )

    def by_role(self, tracker_transforms):
        return {transform.role: transform for transform in tracker_transforms}


class SemanticTrackerAnchorTests(NumericAssertions):
    def target_and_anchors(self, source, target, local_overrides=None, root=None):
        pose = pose_from_local_rotations(
            source,
            local_overrides,
            root_translation=root or (0.0, 1.0, 0.0),
        )
        target_pose = retarget_pose(pose, source, target)
        definitions = synthetic_tracker_anchor_definitions(target)
        return target_pose, self.by_role(
            build_tracker_transforms(target_pose, definitions)
        )

    def test_identity_pose_builds_all_eight_fixture_anchors(self):
        skeleton = synthetic_human_skeleton()
        target_pose, anchors = self.target_and_anchors(skeleton, skeleton)
        self.assertEqual(set(anchors), set(SemanticTrackerRole))
        self.assertEqual(len(anchors), 8)

        expected_positions = {
            SemanticTrackerRole.HIP: (0.0, 1.0, 0.04),
            SemanticTrackerRole.CHEST: (0.0, 1.50, 0.04),
            SemanticTrackerRole.LEFT_KNEE: (-0.1, 0.57, 0.03),
            SemanticTrackerRole.RIGHT_KNEE: (0.1, 0.57, 0.03),
            SemanticTrackerRole.LEFT_FOOT: (-0.1, 0.14, 0.09),
            SemanticTrackerRole.RIGHT_FOOT: (0.1, 0.14, 0.09),
            SemanticTrackerRole.LEFT_UPPER_ARM: (-0.34, 1.53, 0.0),
            SemanticTrackerRole.RIGHT_UPPER_ARM: (0.34, 1.53, 0.0),
        }
        for role, expected in expected_positions.items():
            self.assertVectorAlmostEqual(anchors[role].position, expected)
            self.assertRotationEquivalent(
                anchors[role].rotation, Quaternion.identity()
            )

        self.assertVectorAlmostEqual(
            target_pose.transform("L_Foot").position,
            (-0.1, 0.14, 0.18),
        )

    def test_long_and_short_legs_move_only_lower_body_anchors(self):
        source = synthetic_human_skeleton()
        long_target = synthetic_human_skeleton(upper_leg=0.52, lower_leg=0.50)
        short_target = synthetic_human_skeleton(upper_leg=0.36, lower_leg=0.34)
        _, long_anchors = self.target_and_anchors(source, long_target)
        _, short_anchors = self.target_and_anchors(source, short_target)

        for role in (
            SemanticTrackerRole.HIP,
            SemanticTrackerRole.CHEST,
            SemanticTrackerRole.LEFT_UPPER_ARM,
            SemanticTrackerRole.RIGHT_UPPER_ARM,
        ):
            self.assertVectorAlmostEqual(
                long_anchors[role].position, short_anchors[role].position
            )
        self.assertAlmostEqual(
            short_anchors[SemanticTrackerRole.LEFT_KNEE].position[1]
            - long_anchors[SemanticTrackerRole.LEFT_KNEE].position[1],
            0.16,
            delta=POSITION_TOLERANCE_METRES,
        )
        self.assertAlmostEqual(
            short_anchors[SemanticTrackerRole.LEFT_FOOT].position[1]
            - long_anchors[SemanticTrackerRole.LEFT_FOOT].position[1],
            0.32,
            delta=POSITION_TOLERANCE_METRES,
        )

    def test_knee_bend_rotates_knee_and_foot_offsets_with_their_parents(self):
        skeleton = synthetic_human_skeleton()
        knee_rotation = quaternion_from_axis_angle((1.0, 0.0, 0.0), 90.0)
        target_pose, anchors = self.target_and_anchors(
            skeleton, skeleton, {"L_Knee": knee_rotation}
        )
        knee_parent = target_pose.transform("L_Knee")
        ankle_parent = target_pose.transform("L_Ankle")
        expected_knee = tuple(
            value + offset
            for value, offset in zip(
                knee_parent.position,
                rotate_vector(knee_parent.rotation, (0.0, 0.0, 0.03)),
            )
        )
        expected_foot = tuple(
            value + offset
            for value, offset in zip(
                ankle_parent.position,
                rotate_vector(ankle_parent.rotation, (0.0, 0.0, 0.09)),
            )
        )
        self.assertVectorAlmostEqual(
            anchors[SemanticTrackerRole.LEFT_KNEE].position, expected_knee
        )
        self.assertVectorAlmostEqual(
            anchors[SemanticTrackerRole.LEFT_FOOT].position, expected_foot
        )
        self.assertRotationEquivalent(
            anchors[SemanticTrackerRole.LEFT_KNEE].rotation, knee_rotation
        )
        self.assertRotationEquivalent(
            anchors[SemanticTrackerRole.LEFT_FOOT].rotation, knee_rotation
        )

    def test_root_translation_moves_all_eight_by_the_exact_world_delta(self):
        skeleton = synthetic_human_skeleton()
        source_sequence = synthetic_root_translation_sequence(skeleton)
        all_anchors = []
        for source_pose in source_sequence:
            target_pose = retarget_pose(source_pose, skeleton, skeleton)
            all_anchors.append(
                self.by_role(
                    build_tracker_transforms(
                        target_pose, synthetic_tracker_anchor_definitions(skeleton)
                    )
                )
            )
        baseline = all_anchors[0]
        baseline_root = source_sequence[0].root_translation
        for source_pose, anchors in zip(source_sequence, all_anchors):
            delta = tuple(
                current - base
                for current, base in zip(
                    source_pose.root_translation, baseline_root
                )
            )
            for role in SemanticTrackerRole:
                expected = tuple(
                    value + shift
                    for value, shift in zip(baseline[role].position, delta)
                )
                self.assertVectorAlmostEqual(anchors[role].position, expected)
                self.assertRotationEquivalent(
                    anchors[role].rotation, baseline[role].rotation
                )

    def test_body_yaw_rotates_positions_and_rotations_about_the_root(self):
        skeleton = synthetic_human_skeleton()
        yaw = quaternion_from_axis_angle((0.0, 1.0, 0.0), 90.0)
        _, baseline = self.target_and_anchors(skeleton, skeleton)
        _, rotated = self.target_and_anchors(
            skeleton, skeleton, {"Pelvis": yaw}
        )
        root = (0.0, 1.0, 0.0)
        for role in SemanticTrackerRole:
            relative = tuple(
                value - origin for value, origin in zip(baseline[role].position, root)
            )
            expected_relative = rotate_vector(yaw, relative)
            expected = tuple(
                origin + value for origin, value in zip(root, expected_relative)
            )
            self.assertVectorAlmostEqual(rotated[role].position, expected)
            self.assertRotationEquivalent(rotated[role].rotation, yaw)

    def test_shoulder_width_expands_upper_arm_anchor_span_only_by_width_delta(self):
        source = synthetic_human_skeleton()
        base_target = synthetic_human_skeleton(shoulder_width_scale=1.0)
        wide_target = synthetic_human_skeleton(shoulder_width_scale=1.10)
        _, base = self.target_and_anchors(source, base_target)
        _, wide = self.target_and_anchors(source, wide_target)
        base_span = (
            base[SemanticTrackerRole.RIGHT_UPPER_ARM].position[0]
            - base[SemanticTrackerRole.LEFT_UPPER_ARM].position[0]
        )
        wide_span = (
            wide[SemanticTrackerRole.RIGHT_UPPER_ARM].position[0]
            - wide[SemanticTrackerRole.LEFT_UPPER_ARM].position[0]
        )
        self.assertAlmostEqual(base_span, 0.68, delta=POSITION_TOLERANCE_METRES)
        self.assertAlmostEqual(wide_span, 0.72, delta=POSITION_TOLERANCE_METRES)
        for role in (
            SemanticTrackerRole.HIP,
            SemanticTrackerRole.CHEST,
            SemanticTrackerRole.LEFT_KNEE,
            SemanticTrackerRole.RIGHT_KNEE,
            SemanticTrackerRole.LEFT_FOOT,
            SemanticTrackerRole.RIGHT_FOOT,
        ):
            self.assertVectorAlmostEqual(base[role].position, wide[role].position)

    def test_fixture_hip_width_moves_leg_anchors_symmetrically_not_central_roles(self):
        source = synthetic_human_skeleton()
        base_target = synthetic_human_skeleton(hip_width=0.20)
        wide_target = synthetic_human_skeleton(hip_width=0.24)
        _, base = self.target_and_anchors(source, base_target)
        _, wide = self.target_and_anchors(source, wide_target)

        for role in (
            SemanticTrackerRole.HIP,
            SemanticTrackerRole.CHEST,
            SemanticTrackerRole.LEFT_UPPER_ARM,
            SemanticTrackerRole.RIGHT_UPPER_ARM,
        ):
            self.assertVectorAlmostEqual(base[role].position, wide[role].position)
        for left_role, right_role in (
            (SemanticTrackerRole.LEFT_KNEE, SemanticTrackerRole.RIGHT_KNEE),
            (SemanticTrackerRole.LEFT_FOOT, SemanticTrackerRole.RIGHT_FOOT),
        ):
            self.assertAlmostEqual(
                wide[left_role].position[0] - base[left_role].position[0],
                -0.02,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                wide[right_role].position[0] - base[right_role].position[0],
                0.02,
                delta=POSITION_TOLERANCE_METRES,
            )
            self.assertAlmostEqual(
                wide[left_role].position[1],
                base[left_role].position[1],
                delta=POSITION_TOLERANCE_METRES,
            )

    def test_left_and_right_anchors_are_mirrored_without_role_specific_math(self):
        skeleton = synthetic_human_skeleton()
        symmetric = quaternion_from_axis_angle((1.0, 0.0, 0.0), 35.0)
        _, anchors = self.target_and_anchors(
            skeleton,
            skeleton,
            {
                "L_Hip": symmetric,
                "R_Hip": symmetric,
                "L_Knee": symmetric,
                "R_Knee": symmetric,
            },
        )
        for left_role, right_role in (
            (SemanticTrackerRole.LEFT_KNEE, SemanticTrackerRole.RIGHT_KNEE),
            (SemanticTrackerRole.LEFT_FOOT, SemanticTrackerRole.RIGHT_FOOT),
            (
                SemanticTrackerRole.LEFT_UPPER_ARM,
                SemanticTrackerRole.RIGHT_UPPER_ARM,
            ),
        ):
            left = anchors[left_role]
            right = anchors[right_role]
            self.assertAlmostEqual(left.position[0], -right.position[0], delta=1e-9)
            self.assertAlmostEqual(left.position[1], right.position[1], delta=1e-9)
            self.assertAlmostEqual(left.position[2], right.position[2], delta=1e-9)
            self.assertRotationEquivalent(left.rotation, right.rotation)

    def test_noncommuting_local_rotation_offset_is_parent_times_offset(self):
        skeleton = synthetic_human_skeleton()
        parent_rotation = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        local_offset_rotation = quaternion_from_axis_angle((0.0, 1.0, 0.0), 40.0)
        pose = pose_from_local_rotations(skeleton, {"Pelvis": parent_rotation})
        target_pose = retarget_pose(pose, skeleton, skeleton)
        definitions = list(synthetic_tracker_anchor_definitions(skeleton))
        hip_index = next(
            index
            for index, definition in enumerate(definitions)
            if definition.role is SemanticTrackerRole.HIP
        )
        definitions[hip_index] = replace(
            definitions[hip_index], local_rotation_offset=local_offset_rotation
        )
        hip = self.by_role(build_tracker_transforms(target_pose, definitions))[
            SemanticTrackerRole.HIP
        ]
        expected = quaternion_multiply(parent_rotation, local_offset_rotation)
        rejected_reverse = quaternion_multiply(
            local_offset_rotation, parent_rotation
        )
        self.assertRotationEquivalent(hip.rotation, expected)
        self.assertFalse(quaternions_equivalent(hip.rotation, rejected_reverse))

    def test_definition_validation_rejects_missing_duplicate_and_unknown_parent(self):
        skeleton = synthetic_human_skeleton()
        target_pose = retarget_pose(
            pose_from_local_rotations(skeleton), skeleton, skeleton
        )
        definitions = list(synthetic_tracker_anchor_definitions(skeleton))
        with self.assertRaisesRegex(ValueError, "exactly the 8"):
            build_tracker_transforms(target_pose, definitions[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_tracker_transforms(target_pose, definitions + [definitions[0]])
        definitions[0] = replace(definitions[0], parent_joint="Missing")
        with self.assertRaisesRegex(ValueError, "unknown anchor parent"):
            build_tracker_transforms(target_pose, definitions)

    def test_full_delta_to_target_to_eight_anchor_pipeline(self):
        pelvis_bind = quaternion_from_axis_angle((0.0, 1.0, 0.0), 20.0)
        spine_bind = quaternion_from_axis_angle((1.0, 0.0, 0.0), 10.0)
        source = synthetic_human_skeleton(
            rest_local_rotation_overrides={
                "Pelvis": pelvis_bind,
                "Spine3": spine_bind,
            }
        )
        target = synthetic_human_skeleton(
            upper_leg=0.52,
            lower_leg=0.50,
            shoulder_width_scale=1.10,
        )
        pelvis_motion = quaternion_from_axis_angle((1.0, 0.0, 0.0), 12.0)
        spine_motion = quaternion_from_axis_angle((0.0, 1.0, 0.0), 18.0)
        knee_motion = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        expected_source_pose = pose_from_local_rotations(
            source,
            {
                "Pelvis": quaternion_multiply(pelvis_bind, pelvis_motion),
                "Spine3": quaternion_multiply(spine_bind, spine_motion),
                "L_Knee": knee_motion,
            },
            root_translation=(0.2, 1.1, -0.3),
        )
        source_bind_globals = source_bind_global_rotations(source)
        deltas = tuple(
            quaternion_multiply(source_global, quaternion_inverse(bind_global))
            for source_global, bind_global in zip(
                expected_source_pose.global_rotations, source_bind_globals
            )
        )
        sdk_pose = ReboCapDeltaPose.from_rebocap24((0.2, 1.1, -0.3), deltas)
        canonical_source_pose = adapt_rebocap_delta_pose(sdk_pose, source)
        target_pose = retarget_pose(canonical_source_pose, source, target)
        definitions = synthetic_tracker_anchor_definitions(target)
        anchors = self.by_role(build_tracker_transforms(target_pose, definitions))

        self.assertEqual(len(anchors), 8)
        self.assertEqual(target_pose.transform("Pelvis").position, (0.2, 1.1, -0.3))
        for joint_name in ("Spine3", "L_Knee", "L_Ankle"):
            joint_index = source.index(joint_name)
            self.assertRotationEquivalent(
                canonical_source_pose.global_rotations[joint_index],
                expected_source_pose.global_rotations[joint_index],
            )

        expected_pelvis_rotation = pelvis_motion
        expected_spine_rotation = quaternion_multiply(
            expected_pelvis_rotation, spine_motion
        )
        expected_knee_rotation = quaternion_multiply(
            expected_pelvis_rotation, knee_motion
        )
        root = (0.2, 1.1, -0.3)

        def add_rotated(position, rotation, offset):
            rotated = rotate_vector(rotation, offset)
            return tuple(
                component + shift
                for component, shift in zip(position, rotated)
            )

        expected_spine1_position = add_rotated(
            root, expected_pelvis_rotation, (0.0, 0.15, 0.0)
        )
        expected_spine2_position = add_rotated(
            expected_spine1_position,
            expected_pelvis_rotation,
            (0.0, 0.15, 0.0),
        )
        expected_spine3_position = add_rotated(
            expected_spine2_position,
            expected_pelvis_rotation,
            (0.0, 0.15, 0.0),
        )
        expected_chest_position = add_rotated(
            expected_spine3_position,
            expected_spine_rotation,
            (0.0, 0.05, 0.04),
        )

        expected_left_hip_position = add_rotated(
            root, expected_pelvis_rotation, (-0.10, 0.0, 0.0)
        )
        expected_left_knee_position = add_rotated(
            expected_left_hip_position,
            expected_pelvis_rotation,
            (0.0, -0.52, 0.0),
        )
        expected_left_ankle_position = add_rotated(
            expected_left_knee_position,
            expected_knee_rotation,
            (0.0, -0.50, 0.0),
        )
        expected_knee_anchor_position = add_rotated(
            expected_left_knee_position,
            expected_knee_rotation,
            (0.0, 0.0, 0.03),
        )
        expected_foot_anchor_position = add_rotated(
            expected_left_ankle_position,
            expected_knee_rotation,
            (0.0, 0.0, 0.09),
        )

        self.assertVectorAlmostEqual(
            anchors[SemanticTrackerRole.CHEST].position, expected_chest_position
        )
        self.assertRotationEquivalent(
            anchors[SemanticTrackerRole.CHEST].rotation, expected_spine_rotation
        )
        self.assertVectorAlmostEqual(
            anchors[SemanticTrackerRole.LEFT_KNEE].position,
            expected_knee_anchor_position,
        )
        self.assertRotationEquivalent(
            anchors[SemanticTrackerRole.LEFT_KNEE].rotation,
            expected_knee_rotation,
        )
        self.assertVectorAlmostEqual(
            anchors[SemanticTrackerRole.LEFT_FOOT].position,
            expected_foot_anchor_position,
        )
        self.assertRotationEquivalent(
            anchors[SemanticTrackerRole.LEFT_FOOT].rotation,
            expected_knee_rotation,
        )


if __name__ == "__main__":
    unittest.main()
