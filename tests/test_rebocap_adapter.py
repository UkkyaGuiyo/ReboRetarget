"""Phase 2C tests for the pure ReboCap T-pose-delta adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import math
import unittest
from unittest.mock import patch

from reboretarget import (
    PreparedReboCapAdapter,
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

    def test_prepared_matches_reference_with_noncommuting_binds_and_signs(self):
        skeleton = synthetic_human_skeleton(rest_local_rotation_overrides={
            "Pelvis": quaternion_from_axis_angle((0., 1., 0.), 40.),
            "Spine3": quaternion_from_axis_angle((1., 0., 0.), -17.),
            "L_Shoulder": quaternion_from_axis_angle((0., 0., 1.), 23.),
        })
        prepared = PreparedReboCapAdapter(skeleton)
        for angle in (0., 30., 89.9, 90., 90.1, 179., 180., 181., -179.):
            rotations = tuple(quaternion_from_axis_angle((1., 2., 3.), angle + index)
                              for index in range(24))
            for sign in (1, -1):
                delta = ReboCapDeltaPose.from_rebocap24((.2, 1.1, -.3),
                    rotations if sign == 1 else tuple(value.negated() for value in rotations))
                self.assertEqual(prepared.adapt(delta), adapt_rebocap_delta_pose(delta, skeleton))

    def test_prepared_computes_bind_once_and_is_immutable(self):
        skeleton = synthetic_human_skeleton()
        delta = self.delta_pose(skeleton)
        with patch("reboretarget.rebocap_adapter.source_bind_global_rotations",
                   wraps=source_bind_global_rotations) as bind:
            prepared = PreparedReboCapAdapter(skeleton)
            prepared.adapt(delta)
            prepared.adapt(delta)
            bind.assert_called_once_with(skeleton)
        self.assertIs(prepared.source_bind_skeleton, skeleton)
        with self.assertRaises(FrozenInstanceError):
            prepared.source_bind_skeleton = synthetic_human_skeleton()
        with self.assertRaises(FrozenInstanceError):
            prepared._bind_globals = ()

    def test_prepared_rejects_invalid_static_hierarchy(self):
        skeleton = synthetic_human_skeleton()
        joints = list(skeleton.joints)
        index = skeleton.index("L_Hand")
        joints[index] = replace(joints[index], parent="L_Elbow")
        with self.assertRaisesRegex(ValueError, "parent hierarchy"):
            PreparedReboCapAdapter(SkeletonDefinition(tuple(joints)))

    def test_prepared_preserves_nonunit_input_normalization_and_direct_validation(self):
        skeleton = synthetic_human_skeleton()
        prepared = PreparedReboCapAdapter(skeleton)
        delta = ReboCapDeltaPose((.3, 1., -.2), ((2., -3., 4., -5.),) * 24)
        self.assertEqual(prepared.adapt(delta), adapt_rebocap_delta_pose(delta, skeleton))
        for rotations in (((1., 0., 0., 0.),) * 23, ((0., 0., 0., 0.),) * 24,
                          ((math.nan, 0., 0., 0.),) * 24, ((math.inf, 0., 0., 0.),) * 24):
            with self.assertRaises(ValueError):
                ReboCapDeltaPose((0., 1., 0.), rotations)
        with self.assertRaises(ValueError):
            ReboCapDeltaPose((0., math.inf, 0.), ((1., 0., 0., 0.),) * 24)

    def test_prepared_does_not_skip_dynamic_checks_after_preparation(self):
        skeleton = synthetic_human_skeleton()
        prepared = PreparedReboCapAdapter(skeleton)
        # Deliberately bypass the value constructor to exercise both adapters'
        # dynamic checks; ordinary public construction rejects these earlier.
        for root, rotations in (
            ((0., 1., 0.), (Quaternion.identity(),) * 23),
            ((0., 1., 0.), (Quaternion(0., 0., 0., 0.),) * 24),
            ((0., math.nan, 0.), (Quaternion.identity(),) * 24),
        ):
            malformed = object.__new__(ReboCapDeltaPose)
            object.__setattr__(malformed, "root_translation", root)
            object.__setattr__(malformed, "sdk_global_rotation_deltas", rotations)
            with self.assertRaises(ValueError):
                prepared.adapt(malformed)
            with self.assertRaises(ValueError):
                adapt_rebocap_delta_pose(malformed, skeleton)


if __name__ == "__main__":
    unittest.main()
