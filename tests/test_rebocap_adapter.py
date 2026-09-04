"""Phase 2C tests for the pure ReboCap T-pose-delta adapter."""

from __future__ import annotations

from dataclasses import replace
import unittest

from reboretarget import (
    Quaternion,
    ReboCapDeltaPose,
    SkeletonDefinition,
    adapt_rebocap_delta_pose,
    global_to_local_rotations,
    quaternion_from_axis_angle,
    quaternion_inverse,
    quaternion_multiply,
    quaternions_equivalent,
    source_bind_global_rotations,
)
from tests.synthetic_fixtures import synthetic_human_skeleton


ROTATION_TOLERANCE = 1e-9


class ReboCapAdapterTests(unittest.TestCase):
    def assertRotationEquivalent(self, actual, expected):
        self.assertTrue(
            quaternions_equivalent(actual, expected, tolerance=ROTATION_TOLERANCE),
            msg=f"rotations differ: {actual!r} != {expected!r}",
        )

    def delta_pose(self, skeleton, overrides=None, root=(0.0, 1.0, 0.0)):
        rotations = [Quaternion.identity()] * 24
        for name, rotation in (overrides or {}).items():
            rotations[skeleton.index(name)] = rotation
        return ReboCapDeltaPose.from_rebocap24(root, rotations)

    def test_identity_bind_and_identity_delta_produce_identity_globals(self):
        skeleton = synthetic_human_skeleton()
        adapted = adapt_rebocap_delta_pose(
            self.delta_pose(skeleton, root=(0.2, 1.1, -0.3)), skeleton
        )
        self.assertEqual(adapted.root_translation, (0.2, 1.1, -0.3))
        for rotation in adapted.global_rotations:
            self.assertRotationEquivalent(rotation, Quaternion.identity())

    def test_nonidentity_bind_and_identity_delta_reproduce_bind_globals(self):
        skeleton = synthetic_human_skeleton(
            rest_local_rotation_overrides={
                "Pelvis": quaternion_from_axis_angle((0.0, 1.0, 0.0), 20.0),
                "Spine1": quaternion_from_axis_angle((1.0, 0.0, 0.0), 12.0),
                "L_Hip": quaternion_from_axis_angle((0.0, 0.0, 1.0), 15.0),
            }
        )
        bind_globals = source_bind_global_rotations(skeleton)
        adapted = adapt_rebocap_delta_pose(self.delta_pose(skeleton), skeleton)
        for actual, expected in zip(adapted.global_rotations, bind_globals):
            self.assertRotationEquivalent(actual, expected)

    def test_identity_bind_and_30_degree_delta_produce_that_global(self):
        skeleton = synthetic_human_skeleton()
        delta = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        adapted = adapt_rebocap_delta_pose(
            self.delta_pose(skeleton, {"L_Hip": delta}), skeleton
        )
        self.assertRotationEquivalent(
            adapted.global_rotations[skeleton.index("L_Hip")], delta
        )

    def test_nonidentity_bind_uses_delta_times_bind_in_noncommuting_order(self):
        bind = quaternion_from_axis_angle((0.0, 1.0, 0.0), 40.0)
        delta = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        skeleton = synthetic_human_skeleton(
            rest_local_rotation_overrides={"Pelvis": bind}
        )
        adapted = adapt_rebocap_delta_pose(
            self.delta_pose(skeleton, {"Pelvis": delta}), skeleton
        )
        actual = adapted.global_rotations[skeleton.index("Pelvis")]
        expected = quaternion_multiply(delta, bind)
        rejected_reverse = quaternion_multiply(bind, delta)
        self.assertRotationEquivalent(actual, expected)
        self.assertFalse(quaternions_equivalent(actual, rejected_reverse))

    def test_parent_bind_and_child_motion_delta_recover_expected_local(self):
        pelvis_bind = quaternion_from_axis_angle((0.0, 1.0, 0.0), 20.0)
        hip_bind_local = quaternion_from_axis_angle((0.0, 0.0, 1.0), 15.0)
        parent_delta = quaternion_from_axis_angle((1.0, 0.0, 0.0), 10.0)
        child_delta = quaternion_from_axis_angle((1.0, 0.0, 0.0), 30.0)
        skeleton = synthetic_human_skeleton(
            rest_local_rotation_overrides={
                "Pelvis": pelvis_bind,
                "L_Hip": hip_bind_local,
            }
        )
        bind_globals = source_bind_global_rotations(skeleton)
        adapted = adapt_rebocap_delta_pose(
            self.delta_pose(
                skeleton,
                {"Pelvis": parent_delta, "L_Hip": child_delta},
            ),
            skeleton,
        )
        pelvis_index = skeleton.index("Pelvis")
        hip_index = skeleton.index("L_Hip")
        expected_parent_global = quaternion_multiply(
            parent_delta, bind_globals[pelvis_index]
        )
        expected_child_global = quaternion_multiply(
            child_delta, bind_globals[hip_index]
        )
        self.assertRotationEquivalent(
            adapted.global_rotations[pelvis_index], expected_parent_global
        )
        self.assertRotationEquivalent(
            adapted.global_rotations[hip_index], expected_child_global
        )

        recovered_locals = global_to_local_rotations(
            skeleton, adapted.global_rotations
        )
        expected_child_local = quaternion_multiply(
            quaternion_inverse(expected_parent_global), expected_child_global
        )
        self.assertRotationEquivalent(recovered_locals[hip_index], expected_child_local)

    def test_adapter_rejects_wrong_hierarchy_and_delta_count(self):
        skeleton = synthetic_human_skeleton()
        joints = list(skeleton.joints)
        hand_index = skeleton.index("L_Hand")
        joints[hand_index] = replace(joints[hand_index], parent="L_Elbow")
        wrong = SkeletonDefinition(tuple(joints))
        pose = self.delta_pose(skeleton)
        with self.assertRaisesRegex(ValueError, "parent hierarchy"):
            adapt_rebocap_delta_pose(pose, wrong)
        with self.assertRaisesRegex(ValueError, "exactly 24"):
            ReboCapDeltaPose(
                (0.0, 1.0, 0.0),
                (Quaternion.identity(),) * 23,
            )


if __name__ == "__main__":
    unittest.main()
