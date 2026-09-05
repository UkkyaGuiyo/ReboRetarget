"""Synthetic only: no SDK, clocks, processes, I/O, or recorded motion."""

import json
import unittest
from dataclasses import replace

from reboretarget import (
    Quaternion, SourcePose, ReboCapDeltaPose, quaternion_from_axis_angle,
    quaternion_multiply, quaternion_inverse, retarget_pose,
    build_tracker_transforms, synthetic_tracker_anchor_definitions,
)
from reboretarget.rebocap_adapter import source_bind_global_rotations
from research.controlled_motion_analysis import MotionFrame, analyze_cue, axis_angle, clean_cue_result
from tests.synthetic_fixtures import synthetic_human_skeleton, pose_from_local_rotations


class ControlledMotionAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.bind = synthetic_human_skeleton()

    def frame(self, overrides=None, root=(0., 1., 0.), negate=False):
        canonical = pose_from_local_rotations(self.bind, overrides, root_translation=root)
        binds = source_bind_global_rotations(self.bind)
        deltas = tuple(quaternion_multiply(q, quaternion_inverse(b))
                       for q, b in zip(canonical.global_rotations, binds))
        if negate:
            deltas = tuple(q.negated() for q in deltas)
        delta = ReboCapDeltaPose(root, deltas)
        target = retarget_pose(canonical, self.bind, self.bind)
        anchors = build_tracker_transforms(target, synthetic_tracker_anchor_definitions(self.bind))
        return MotionFrame(delta, canonical, anchors)

    def run_cue(self, cue, held, returned=None, baseline=None):
        neutral = self.frame()
        result = analyze_cue(cue, [baseline or neutral]*60, [held]*20,
                             [returned or neutral]*20, self.bind)
        self.assertEqual(clean_cue_result(result), result)
        return result

    def test_translation_axis_sign_and_target_propagation(self):
        for cue, root, axis, sign in (("right", (.3,1.,0.), "X",1),
                ("forward", (0.,1.,-.3),"Z",-1), ("crouch",(0.,.8,0.),"Y",-1)):
            with self.subTest(cue=cue):
                result = self.run_cue(cue, self.frame(root=root))
                self.assertEqual(result["result"], "FAIL" if cue == "forward" else "PASS")
                self.assertEqual(result["translation"]["dominant_axis"], axis)
                self.assertEqual(result["translation"]["sign"], sign)
                self.assertNotEqual(result["confidence"], "CONFIRMED")
                for anchor in result["anchors"].values():
                    for got, expected in zip(anchor["delta_xyz_m"], result["translation"]["delta_xyz_m"]):
                        self.assertAlmostEqual(got, expected)

    def test_weak_mixed_axis_nonreturn_are_unverified(self):
        for root, returned in (((.001,1.,0.), None), ((.3,1.,.3),None),
                               ((.3,1.,0.),self.frame(root=(.3,1.,0.)))):
            self.assertEqual(self.run_cue("right", self.frame(root=root), returned)["result"], "UNVERIFIED")

    def test_noisy_baseline_and_moving_hold_are_unverified(self):
        neutral = self.frame()
        noisy = [self.frame(root=((-.2 if i%2 else .2),1.,0.)) for i in range(60)]
        result = analyze_cue("right", noisy, [self.frame(root=(.3,1.,0.))]*20, [neutral]*20, self.bind)
        self.assertEqual(result["result"], "UNVERIFIED")
        moving = [self.frame(root=(.0 if i%2 else .6,1.,0.)) for i in range(20)]
        self.assertEqual(analyze_cue("right", [neutral]*60, moving, [neutral]*20, self.bind)["result"], "UNVERIFIED")

    def test_yaw_left_right_sign_and_no_euler(self):
        for cue, degrees in (("yaw_left",-35), ("yaw_right",35)):
            result = self.run_cue(cue, self.frame({"Pelvis": quaternion_from_axis_angle((0,1,0),degrees)}))
            self.assertEqual(result["result"], "PASS")
            self.assertAlmostEqual(result["yaw"]["signed_deg"], degrees)
            self.assertEqual(result["adapter"]["result"], "PASS")

    def test_knee_local_motion_and_inherited_ankle(self):
        for side, cue in (("L","left_knee"),("R","right_knee")):
            result = self.run_cue(cue, self.frame({side+"_Knee": quaternion_from_axis_angle((1,0,0),30)}))
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["side_response"]["joint"], side+"_Knee")
            self.assertAlmostEqual(result["joints"][side+"_Ankle"]["local_change"]["angle_deg"],0)
            self.assertAlmostEqual(result["pair_global_distance_deg"]["held"][side+"_Ankle/"+side+"_Foot"]["max"],0)
        inherited = self.run_cue("left_knee", self.frame({"L_Hip": quaternion_from_axis_angle((1,0,0),30)}))
        self.assertEqual(inherited["result"], "UNVERIFIED")

    def test_wrong_side_knee_is_not_accepted(self):
        result = self.run_cue("left_knee", self.frame({"R_Knee":quaternion_from_axis_angle((1,0,0),30)}))
        self.assertEqual(result["result"], "FAIL")

    def test_noisy_or_nonreturning_opposite_knee_is_unverified(self):
        def knee(degrees):
            return self.frame({"R_Knee":quaternion_from_axis_angle((1,0,0),degrees)})
        neutral = self.frame()
        noisy_baseline = [knee(-10 if i % 2 else 10) for i in range(60)]
        result = analyze_cue("left_knee", noisy_baseline, [knee(5)]*20,
                             [neutral]*20, self.bind)
        self.assertAlmostEqual(result["joints"]["R_Knee"]["local_threshold_deg"], 30)
        self.assertEqual(result["result"], "UNVERIFIED")
        result = self.run_cue("left_knee", knee(30), returned=knee(30))
        self.assertEqual(result["result"], "UNVERIFIED")
        moving_hold = [knee(0 if i % 2 else 60) for i in range(20)]
        result = analyze_cue("left_knee", [neutral]*60, moving_hold,
                             [neutral]*20, self.bind)
        self.assertEqual(result["result"], "UNVERIFIED")

    def test_arm_shoulder_and_inheritance_no_sensor_ownership(self):
        for cue, side in (("left_arm","L"),("right_arm","R"),("left_shoulder","L"),("right_shoulder","R")):
            result = self.run_cue(cue, self.frame({side+"_Shoulder": quaternion_from_axis_angle((0,1,0),25)}))
            self.assertEqual(result["result"], "PASS")
            self.assertAlmostEqual(result["pair_global_distance_deg"]["held"][side+"_Shoulder/"+side+"_Elbow"]["max"],0)
            self.assertAlmostEqual(result["joints"][side+"_Elbow"]["local_change"]["angle_deg"],0)
            self.assertNotIn("sensor", json.dumps(result))

    def test_nonidentity_bind_and_q_sign_motion_invariant(self):
        self.bind = synthetic_human_skeleton(rest_local_rotation_overrides={
            "Pelvis": quaternion_from_axis_angle((1,0,0),25),
            "L_Shoulder": quaternion_from_axis_angle((0,0,1),35)})
        result = self.run_cue("left_arm",self.frame({"L_Shoulder":quaternion_from_axis_angle((0,1,0),50)}, negate=True))
        self.assertEqual(result["adapter"]["result"], "PASS")
        self.assertLess(result["adapter"]["max_motion_error_deg"],1e-6)
        for degrees in (0, 90, 179, 180, 181):
            q = quaternion_from_axis_angle((1,2,3), degrees)
            a, b = axis_angle(Quaternion.identity(),q), axis_angle(Quaternion.identity(),q.negated())
            self.assertEqual(a,b)

    def test_constant_wrong_bind_is_detected_even_motion_equivalent(self):
        neutral = self.frame()
        wrong = quaternion_from_axis_angle((1,0,0),20)
        def corrupt(frame):
            pose = SourcePose(frame.canonical.root_translation,
                tuple(quaternion_multiply(q,wrong) for q in frame.canonical.global_rotations))
            return replace(frame, canonical=pose)
        held = self.frame(root=(.3,1.,0.))
        result = analyze_cue("right", [corrupt(neutral)]*60, [corrupt(held)]*20,
                             [corrupt(neutral)]*20,self.bind)
        self.assertEqual(result["adapter"]["result"],"FAIL")
        self.assertEqual(result["result"],"FAIL")

    def test_window_bounds_missing_samples_and_finite_schema(self):
        neutral = self.frame()
        result = analyze_cue("right",[neutral]*59,[neutral]*20,[neutral]*20,self.bind)
        self.assertEqual(result["result"],"INCOMPLETE")
        with self.assertRaises(ValueError):
            analyze_cue("right",[neutral]*61,[],[],self.bind)
        with self.assertRaises(ValueError):
            analyze_cue("unknown",[],[],[],self.bind)
        with self.assertRaises(ValueError):
            replace(neutral,anchors=neutral.anchors[:7])
        result = self.run_cue("right", self.frame(root=(.3,1.,0.)))
        encoded = json.dumps(result, allow_nan=False)
        self.assertEqual(clean_cue_result(result),result)
        for forbidden in ("timestamp", "sequence", "frames", "sdk_path", "process_id"):
            self.assertNotIn(forbidden, encoded)

    def test_strict_ipc_allowlist_rejects_extra_raw_nonfinite_and_wrong_shapes(self):
        import copy
        result = self.run_cue("left_knee",self.frame({"L_Knee":quaternion_from_axis_angle((1,0,0),30)}))
        self.assertEqual(clean_cue_result(result),result)
        for mutate in (
            lambda d: d.update(raw_pose=[1,2,3]),
            lambda d: d["counts"].update(callback_timestamp=42),
            lambda d: d["translation"].update(magnitude_m=float("nan")),
            lambda d: d.update(cue="private string"),
            lambda d: d["counts"].update(baseline=True),
            lambda d: d["anchors"].update(arbitrary={}),
            lambda d: d["joints"]["Pelvis"].update(raw=[1]*24),
        ):
            broken = copy.deepcopy(result)
            mutate(broken)
            with self.assertRaises(ValueError):
                clean_cue_result(broken)
        neutral = self.frame()
        incomplete = analyze_cue("right",[neutral],[],[],self.bind)
        self.assertEqual(clean_cue_result(incomplete),incomplete)


if __name__ == "__main__":
    unittest.main()
