"""Independent analytic arm geometry; synthetic only, no SDK or runtime."""

import math
import unittest

from reboretarget import (
    arm_lengths_from_controls, build_tracker_transforms,
    quaternion_from_axis_angle, quaternions_equivalent, retarget_pose,
    synthetic_tracker_anchor_definitions,
)
from tests.synthetic_fixtures import synthetic_human_skeleton, pose_from_local_rotations


class ArmMorphologyTests(unittest.TestCase):
    def assertVector(self, actual, expected):
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want, delta=1e-9)

    def test_total_scale_and_fixed_total_balance(self):
        for scale in (.8, 1., 1.2):
            for balance in (-.1, 0., .1):
                with self.subTest(scale=scale, balance=balance):
                    upper, lower = arm_lengths_from_controls(
                        .28, .25, arm_length=scale, upper_arm_forearm_balance=balance)
                    self.assertAlmostEqual(upper + lower, .53 * scale)
                    self.assertAlmostEqual(upper, (.28 + .53 * balance) * scale)
                    self.assertAlmostEqual(lower, (.25 - .53 * balance) * scale)

    def test_invalid_and_unrepresentable_lengths_rejected(self):
        for field in ("source_upper_arm", "source_forearm", "arm_length"):
            for value in (0., -1., math.nan, math.inf, -math.inf):
                args = dict(source_upper_arm=.28, source_forearm=.25, arm_length=1.)
                args[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    arm_lengths_from_controls(**args)
        for balance in (-1., 1., math.nan, math.inf):
            with self.assertRaises(ValueError):
                arm_lengths_from_controls(.28, .25, upper_arm_forearm_balance=balance)
        for upper, lower, scale in ((1e308, 1e308, 1.), (.28, .25, 1e-323),
                                    (1., 1., 1e308)):
            with self.assertRaises(ValueError):
                arm_lengths_from_controls(upper, lower, arm_length=scale)

    def test_fixture_rejects_invalid_arm_lengths(self):
        for field in ("upper_arm", "forearm"):
            for value in (0., -1., math.nan, math.inf):
                with self.assertRaises(ValueError):
                    synthetic_human_skeleton(**{field: value})

    def test_balance_moves_elbow_but_not_straight_wrist_or_shoulder(self):
        source = synthetic_human_skeleton()
        neutral = pose_from_local_rotations(source)
        original = retarget_pose(neutral, source, source)
        upper, lower = arm_lengths_from_controls(.28, .25, upper_arm_forearm_balance=.1)
        target = synthetic_human_skeleton(upper_arm=upper, forearm=lower)
        result = retarget_pose(neutral, source, target)
        for side, sign in (("L", -1), ("R", 1)):
            for joint in ("Shoulder", "Wrist", "Hand"):
                self.assertVector(result.transform(side+"_"+joint).position,
                                  original.transform(side+"_"+joint).position)
            delta = tuple(a-b for a,b in zip(result.transform(side+"_Elbow").position,
                                           original.transform(side+"_Elbow").position))
            self.assertVector(delta, (sign*.053, 0., 0.))

    def test_bent_elbow_uses_target_lengths_and_preserves_rotation(self):
        source = synthetic_human_skeleton()
        upper, lower = arm_lengths_from_controls(.28, .25, arm_length=1.2,
                                                 upper_arm_forearm_balance=.1)
        target = synthetic_human_skeleton(upper_arm=upper, forearm=lower)
        for side, sign in (("L", -1), ("R", 1)):
            q = quaternion_from_axis_angle((0., 1., 0.), -sign*90.)
            pose = pose_from_local_rotations(source, {side+"_Elbow": q})
            result = retarget_pose(pose, source, target)
            self.assertTrue(quaternions_equivalent(result.local_rotation(side+"_Elbow"), q))
            # Mirrored upper arms along X, both forearms bent toward +Z.
            shoulder = (sign*.2, 1.53, 0.)
            self.assertVector(result.transform(side+"_Shoulder").position, shoulder)
            self.assertVector(result.transform(side+"_Elbow").position,
                              (shoulder[0]+sign*upper, 1.53, 0.))
            self.assertVector(result.transform(side+"_Wrist").position,
                              (shoulder[0]+sign*upper, 1.53, lower))

    def test_forearm_only_change_does_not_move_eight_body_trackers(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(forearm=.4)
        pose = pose_from_local_rotations(source, {
            "L_Elbow": quaternion_from_axis_angle((0.,1.,0.), 65.)})
        a, b = (retarget_pose(pose, source, skeleton) for skeleton in (source, target))
        anchors_a = build_tracker_transforms(a, synthetic_tracker_anchor_definitions(source))
        anchors_b = build_tracker_transforms(b, synthetic_tracker_anchor_definitions(target))
        self.assertEqual(anchors_a, anchors_b)
        self.assertNotEqual(a.transform("L_Wrist").position, b.transform("L_Wrist").position)
