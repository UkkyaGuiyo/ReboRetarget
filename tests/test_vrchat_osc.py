"""Offline tests for VRChat OSC tracker representation and byte encoding."""

from __future__ import annotations

from dataclasses import replace
import math
import struct
import unittest

from reboretarget import (
    DEFAULT_TRACKER_SLOT_MAPPINGS,
    HEAD_POSITION_ADDRESS,
    HEAD_ROTATION_ADDRESS,
    OSC_FLOAT3_TYPE_TAG,
    HeadAlignmentReference,
    OscFloat3Message,
    OscTrackerPose,
    Quaternion,
    ReboCapDeltaPose,
    SEMANTIC_TRACKER_ROLES,
    SemanticTrackerRole,
    TrackerSlotMapping,
    TrackerTransform,
    TrackingSpaceAlignment,
    adapt_rebocap_delta_pose,
    apply_tracking_space_alignment,
    build_head_alignment_messages,
    build_osc_tracker_poses,
    build_tracker_messages,
    build_tracker_transforms,
    decode_osc_float3_message,
    encode_osc_float3_message,
    quaternion_from_axis_angle,
    quaternion_inverse,
    quaternion_multiply,
    quaternion_to_vrchat_euler_degrees,
    quaternions_equivalent,
    retarget_pose,
    rotate_vector,
    source_bind_global_rotations,
    synthetic_tracker_anchor_definitions,
    tracker_position_address,
    tracker_rotation_address,
    validate_tracker_slot_mappings,
    vrchat_euler_degrees_to_quaternion,
)
from tests.synthetic_fixtures import (
    pose_from_local_rotations,
    synthetic_human_skeleton,
)


ROTATION_TOLERANCE = 1e-9
POSITION_TOLERANCE_METRES = 1e-9
FLOAT32_TOLERANCE = 1e-5


def compose_vrchat_rotation(x_degrees, y_degrees, z_degrees):
    """Independent test construction for fixed-world-axis Z, X, Y order."""

    qx = quaternion_from_axis_angle((1.0, 0.0, 0.0), x_degrees)
    qy = quaternion_from_axis_angle((0.0, 1.0, 0.0), y_degrees)
    qz = quaternion_from_axis_angle((0.0, 0.0, 1.0), z_degrees)
    return quaternion_multiply(qy, quaternion_multiply(qx, qz))


def vector_distance(left, right):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def representative_tracker_transforms():
    return tuple(
        TrackerTransform(
            role,
            (float(index), 1.0 + index * 0.1, -index * 0.2),
            quaternion_from_axis_angle((0.0, 1.0, 0.0), 7.5 * index),
        )
        for index, role in enumerate(SEMANTIC_TRACKER_ROLES)
    )


class VrchatRotationRepresentationTests(unittest.TestCase):
    def assertRotationEquivalent(self, left, right):
        self.assertTrue(
            quaternions_equivalent(left, right, tolerance=ROTATION_TOLERANCE),
            msg=f"rotations differ: {left!r} != {right!r}",
        )

    def test_required_rotations_round_trip_through_vrchat_zxy_convention(self):
        cases = {
            "identity": (0.0, 0.0, 0.0),
            "x_30": (30.0, 0.0, 0.0),
            "y_30": (0.0, 30.0, 0.0),
            "z_30": (0.0, 0.0, 30.0),
            "x_y": (30.0, 45.0, 0.0),
            "y_z": (0.0, 45.0, 60.0),
            "x_y_z": (30.0, 45.0, 60.0),
            "x_89_9": (89.9, 20.0, -35.0),
            "x_90": (90.0, 20.0, -35.0),
            "x_90_1": (90.1, 20.0, -35.0),
            "y_179": (22.0, 179.0, -31.0),
            "y_180": (22.0, 180.0, -31.0),
            "y_181": (22.0, 181.0, -31.0),
            "y_minus_179": (22.0, -179.0, -31.0),
        }
        for name, source_euler in cases.items():
            with self.subTest(name=name):
                original = compose_vrchat_rotation(*source_euler)
                represented = quaternion_to_vrchat_euler_degrees(original)
                reconstructed = compose_vrchat_rotation(*represented)
                self.assertRotationEquivalent(original, reconstructed)
                self.assertTrue(all(math.isfinite(value) for value in represented))
                self.assertTrue(-90.0 <= represented[0] <= 90.0)
                self.assertTrue(
                    all(-180.0 <= value < 180.0 for value in represented[1:])
                )

    def test_inverse_helper_reconstructs_fixed_axis_zxy_order(self):
        values = (27.0, -41.0, 63.0)
        expected = compose_vrchat_rotation(*values)
        actual = vrchat_euler_degrees_to_quaternion(values)
        self.assertRotationEquivalent(actual, expected)

    def test_q_and_negative_q_produce_identical_euler_values(self):
        rotation = compose_vrchat_rotation(37.0, -123.0, 81.0)
        self.assertEqual(
            quaternion_to_vrchat_euler_degrees(rotation),
            quaternion_to_vrchat_euler_degrees(rotation.negated()),
        )

    def test_positive_and_negative_gimbal_singularities_are_finite_and_equivalent(self):
        for x_degrees in (90.0, -90.0):
            with self.subTest(x_degrees=x_degrees):
                original = compose_vrchat_rotation(x_degrees, 73.0, -127.0)
                represented = quaternion_to_vrchat_euler_degrees(original)
                self.assertTrue(all(math.isfinite(value) for value in represented))
                self.assertEqual(represented[2], 0.0)
                self.assertRotationEquivalent(
                    original, vrchat_euler_degrees_to_quaternion(represented)
                )

    def test_rotation_conversion_rejects_nonfinite_and_zero_quaternions(self):
        with self.assertRaisesRegex(ValueError, "non-zero"):
            quaternion_to_vrchat_euler_degrees(Quaternion(0.0, 0.0, 0.0, 0.0))
        with self.assertRaisesRegex(ValueError, "finite"):
            vrchat_euler_degrees_to_quaternion((0.0, math.inf, 0.0))


class TrackerRepresentationTests(unittest.TestCase):
    def test_default_mapping_is_internal_transport_order_not_role_identity(self):
        expected = (
            (SemanticTrackerRole.HIP, 1),
            (SemanticTrackerRole.CHEST, 2),
            (SemanticTrackerRole.LEFT_KNEE, 3),
            (SemanticTrackerRole.RIGHT_KNEE, 4),
            (SemanticTrackerRole.LEFT_FOOT, 5),
            (SemanticTrackerRole.RIGHT_FOOT, 6),
            (SemanticTrackerRole.LEFT_UPPER_ARM, 7),
            (SemanticTrackerRole.RIGHT_UPPER_ARM, 8),
        )
        self.assertEqual(
            tuple(
                (mapping.role, mapping.slot)
                for mapping in DEFAULT_TRACKER_SLOT_MAPPINGS
            ),
            expected,
        )
        self.assertTrue(
            all(type(mapping.slot) is int for mapping in DEFAULT_TRACKER_SLOT_MAPPINGS)
        )

    def test_mapping_is_replaceable_data_and_output_is_sorted_by_slot(self):
        custom = tuple(
            TrackerSlotMapping(role, 8 - index)
            for index, role in enumerate(SEMANTIC_TRACKER_ROLES)
        )
        transforms = representative_tracker_transforms()
        by_role = {transform.role: transform for transform in transforms}
        poses = build_osc_tracker_poses(transforms, custom)
        self.assertEqual(tuple(pose.slot for pose in poses), tuple(range(1, 9)))
        role_for_slot_one = custom[-1].role
        self.assertEqual(poses[0].position_xyz_m, by_role[role_for_slot_one].position)

    def test_mapping_rejects_missing_duplicate_out_of_range_and_bool_slots(self):
        with self.assertRaisesRegex(ValueError, "exactly the 8"):
            validate_tracker_slot_mappings(DEFAULT_TRACKER_SLOT_MAPPINGS[:-1])
        duplicate_role = list(DEFAULT_TRACKER_SLOT_MAPPINGS)
        duplicate_role[-1] = TrackerSlotMapping(SemanticTrackerRole.HIP, 8)
        with self.assertRaisesRegex(ValueError, "duplicate semantic role"):
            validate_tracker_slot_mappings(duplicate_role)
        duplicate_slot = list(DEFAULT_TRACKER_SLOT_MAPPINGS)
        duplicate_slot[-1] = TrackerSlotMapping(
            SemanticTrackerRole.RIGHT_UPPER_ARM, 7
        )
        with self.assertRaisesRegex(ValueError, "duplicate slot"):
            validate_tracker_slot_mappings(duplicate_slot)
        for invalid in (0, 9, True, 1.0):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "slot"):
                    TrackerSlotMapping(SemanticTrackerRole.HIP, invalid)

    def test_position_meters_and_unity_axes_pass_through_without_output_inversion(self):
        transforms = representative_tracker_transforms()
        by_role = {transform.role: transform.position for transform in transforms}
        slot_by_role = {
            mapping.role: mapping.slot for mapping in DEFAULT_TRACKER_SLOT_MAPPINGS
        }
        poses = build_osc_tracker_poses(transforms)
        pose_by_slot = {pose.slot: pose for pose in poses}
        for role, original_position in by_role.items():
            self.assertEqual(
                pose_by_slot[slot_by_role[role]].position_xyz_m, original_position
            )

    def test_transform_validation_rejects_missing_and_duplicate_roles(self):
        transforms = representative_tracker_transforms()
        with self.assertRaisesRegex(ValueError, "exactly the 8"):
            build_osc_tracker_poses(transforms[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate tracker role"):
            build_osc_tracker_poses(transforms[:-1] + (transforms[0],))

    def test_tracker_addresses_cover_only_slots_one_through_eight(self):
        self.assertEqual(
            tracker_position_address(1), "/tracking/trackers/1/position"
        )
        self.assertEqual(
            tracker_rotation_address(8), "/tracking/trackers/8/rotation"
        )
        for invalid in (0, 9, True):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "slot"):
                    tracker_position_address(invalid)

    def test_tracker_message_builder_rejects_missing_and_duplicate_slots(self):
        poses = build_osc_tracker_poses(representative_tracker_transforms())
        with self.assertRaisesRegex(ValueError, "every slot"):
            build_tracker_messages(poses[:-1])
        duplicate = poses[:-1] + (replace(poses[-1], slot=poses[-2].slot),)
        with self.assertRaisesRegex(ValueError, "duplicate slot"):
            build_tracker_messages(duplicate)


class TrackingSpaceAlignmentTests(unittest.TestCase):
    def make_transforms(self):
        return tuple(
            TrackerTransform(
                role,
                (index * 0.25 - 0.7, 0.4 + index * 0.17, index * -0.13),
                compose_vrchat_rotation(index * 2.0, index * 5.0, -index * 3.0),
            )
            for index, role in enumerate(SEMANTIC_TRACKER_ROLES)
        )

    def test_yaw_and_translation_apply_one_rigid_transform_to_all_eight(self):
        original = self.make_transforms()
        alignment = TrackingSpaceAlignment((1.0, 0.5, -2.0), 90.0)
        aligned = apply_tracking_space_alignment(original, alignment)
        yaw = quaternion_from_axis_angle((0.0, 1.0, 0.0), 90.0)
        self.assertEqual(tuple(item.role for item in aligned), SEMANTIC_TRACKER_ROLES)
        for before, after in zip(original, aligned):
            rotated = rotate_vector(yaw, before.position)
            expected_position = tuple(
                component + translation
                for component, translation in zip(rotated, (1.0, 0.5, -2.0))
            )
            for actual, expected in zip(after.position, expected_position):
                self.assertAlmostEqual(
                    actual, expected, delta=POSITION_TOLERANCE_METRES
                )
            self.assertTrue(
                quaternions_equivalent(
                    after.rotation,
                    quaternion_multiply(yaw, before.rotation),
                    tolerance=ROTATION_TOLERANCE,
                )
            )

    def test_alignment_preserves_body_morphology_and_relative_rotation(self):
        original = self.make_transforms()
        aligned = apply_tracking_space_alignment(
            original, TrackingSpaceAlignment((1.0, 0.5, -2.0), 90.0)
        )
        for left_index in range(len(original)):
            for right_index in range(left_index + 1, len(original)):
                before_distance = vector_distance(
                    original[left_index].position, original[right_index].position
                )
                after_distance = vector_distance(
                    aligned[left_index].position, aligned[right_index].position
                )
                self.assertAlmostEqual(
                    before_distance, after_distance, delta=POSITION_TOLERANCE_METRES
                )
                before_relative = quaternion_multiply(
                    quaternion_inverse(original[left_index].rotation),
                    original[right_index].rotation,
                )
                after_relative = quaternion_multiply(
                    quaternion_inverse(aligned[left_index].rotation),
                    aligned[right_index].rotation,
                )
                self.assertTrue(
                    quaternions_equivalent(
                        before_relative,
                        after_relative,
                        tolerance=ROTATION_TOLERANCE,
                    )
                )

    def test_alignment_rejects_nonfinite_values(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            TrackingSpaceAlignment((0.0, math.nan, 0.0), 0.0)
        with self.assertRaisesRegex(ValueError, "finite"):
            TrackingSpaceAlignment((0.0, 0.0, 0.0), math.inf)


class HeadAlignmentRepresentationTests(unittest.TestCase):
    def test_head_messages_are_separate_from_eight_body_slots(self):
        body_poses = build_osc_tracker_poses(representative_tracker_transforms())
        body_messages = build_tracker_messages(body_poses)
        head_messages = build_head_alignment_messages(
            HeadAlignmentReference(
                position_xyz_m=(0.1, 1.7, -0.2),
                rotation=compose_vrchat_rotation(0.0, 35.0, 0.0),
            )
        )
        self.assertEqual(len(body_messages), 16)
        self.assertEqual(
            tuple(message.address for message in head_messages),
            (HEAD_POSITION_ADDRESS, HEAD_ROTATION_ADDRESS),
        )
        self.assertTrue(
            all("/head/" not in message.address for message in body_messages)
        )

    def test_head_position_or_rotation_can_be_represented_independently(self):
        position_only = build_head_alignment_messages(
            HeadAlignmentReference(position_xyz_m=(0.0, 1.6, 0.0))
        )
        rotation_only = build_head_alignment_messages(
            HeadAlignmentReference(rotation=compose_vrchat_rotation(0.0, 15.0, 0.0))
        )
        self.assertEqual(
            tuple(item.address for item in position_only), (HEAD_POSITION_ADDRESS,)
        )
        self.assertEqual(
            tuple(item.address for item in rotation_only), (HEAD_ROTATION_ADDRESS,)
        )
        with self.assertRaisesRegex(ValueError, "position or rotation"):
            HeadAlignmentReference()


class OscFloat3CodecTests(unittest.TestCase):
    def assertFloat3AlmostEqual(self, left, right):
        for actual, expected in zip(left, right):
            self.assertAlmostEqual(actual, expected, delta=FLOAT32_TOLERANCE)

    def test_required_position_and_rotation_values_encode_decode_in_memory(self):
        cases = (
            ("/tracking/trackers/1/position", (0.0, 0.0, 0.0)),
            ("/tracking/trackers/2/position", (1.0, 2.0, 3.0)),
            ("/tracking/trackers/3/position", (-1.5, 0.25, 7.75)),
            ("/tracking/trackers/4/rotation", (0.0, 0.0, 0.0)),
            ("/tracking/trackers/5/rotation", (30.0, 45.0, 60.0)),
            ("/tracking/trackers/6/rotation", (-179.0, 90.0, 180.0)),
        )
        for address, values in cases:
            with self.subTest(address=address, values=values):
                original = OscFloat3Message(address, values)
                decoded = decode_osc_float3_message(
                    encode_osc_float3_message(original)
                )
                self.assertEqual(decoded.address, address)
                self.assertFloat3AlmostEqual(decoded.values, values)

    def test_encoder_uses_nul_padding_exact_type_tag_and_big_endian_float32(self):
        message = OscFloat3Message("/abc", (1.0, -2.0, 0.25))
        encoded = encode_osc_float3_message(message)
        self.assertEqual(
            encoded,
            b"/abc\0\0\0\0"
            + b",fff\0\0\0\0"
            + struct.pack(">fff", 1.0, -2.0, 0.25),
        )
        self.assertEqual(len(encoded) % 4, 0)
        self.assertEqual(OSC_FLOAT3_TYPE_TAG, ",fff")

    def test_codec_rejects_bad_padding_tag_length_nonfinite_and_address(self):
        valid = encode_osc_float3_message(OscFloat3Message("/abc", (1.0, 2.0, 3.0)))
        bad_padding = valid[:5] + b"x" + valid[6:]
        with self.assertRaisesRegex(ValueError, "padding"):
            decode_osc_float3_message(bad_padding)
        wrong_tag = b"/abc\0\0\0\0" + b",ffi\0\0\0\0" + valid[-12:]
        with self.assertRaisesRegex(ValueError, "exactly ',fff'"):
            decode_osc_float3_message(wrong_tag)
        with self.assertRaisesRegex(ValueError, "exactly 12"):
            decode_osc_float3_message(valid[:-1])
        with self.assertRaisesRegex(ValueError, "exactly 12"):
            decode_osc_float3_message(valid + b"\0")
        nonfinite = valid[:-12] + struct.pack(">fff", math.nan, 2.0, 3.0)
        with self.assertRaisesRegex(ValueError, "finite"):
            decode_osc_float3_message(nonfinite)
        invalid_address = b"abc\0" + b",fff\0\0\0\0" + valid[-12:]
        with self.assertRaisesRegex(ValueError, "beginning"):
            decode_osc_float3_message(invalid_address)

    def test_encoder_rejects_non_ascii_nul_and_float32_overflow(self):
        for address in ("not/an/address", "/bad\0address", "/追跡"):
            with self.subTest(address=address):
                with self.assertRaisesRegex(ValueError, "OSC address"):
                    OscFloat3Message(address, (0.0, 0.0, 0.0))
        with self.assertRaisesRegex(ValueError, "float32"):
            encode_osc_float3_message(OscFloat3Message("/a", (1e100, 0.0, 0.0)))


class FullOfflineSnapshotTests(unittest.TestCase):
    def test_phase2c_synthetic_pipeline_produces_sixteen_decodable_messages(self):
        source = synthetic_human_skeleton()
        target = synthetic_human_skeleton(
            upper_leg=0.52,
            lower_leg=0.50,
            shoulder_width_scale=1.10,
        )
        expected_source_pose = pose_from_local_rotations(
            source,
            {
                "Pelvis": compose_vrchat_rotation(12.0, 24.0, -8.0),
                "Spine3": compose_vrchat_rotation(-9.0, 17.0, 11.0),
                "L_Knee": compose_vrchat_rotation(37.0, 2.0, -4.0),
            },
            root_translation=(0.2, 1.1, -0.3),
        )
        bind_globals = source_bind_global_rotations(source)
        sdk_deltas = tuple(
            quaternion_multiply(expected, quaternion_inverse(bind))
            for expected, bind in zip(
                expected_source_pose.global_rotations, bind_globals
            )
        )
        canonical = adapt_rebocap_delta_pose(
            ReboCapDeltaPose.from_rebocap24(
                expected_source_pose.root_translation, sdk_deltas
            ),
            source,
        )
        target_pose = retarget_pose(canonical, source, target)
        tracker_transforms = build_tracker_transforms(
            target_pose, synthetic_tracker_anchor_definitions(target)
        )
        tracker_poses = build_osc_tracker_poses(tracker_transforms)
        messages = build_tracker_messages(tracker_poses)
        decoded = tuple(
            decode_osc_float3_message(encode_osc_float3_message(message))
            for message in messages
        )

        self.assertEqual(len(tracker_transforms), 8)
        self.assertEqual(len(tracker_poses), 8)
        transform_by_role = {
            transform.role: transform for transform in tracker_transforms
        }
        pose_by_slot = {pose.slot: pose for pose in tracker_poses}
        for mapping in DEFAULT_TRACKER_SLOT_MAPPINGS:
            self.assertTrue(
                quaternions_equivalent(
                    transform_by_role[mapping.role].rotation,
                    vrchat_euler_degrees_to_quaternion(
                        pose_by_slot[mapping.slot].rotation_euler_xyz_deg
                    ),
                    tolerance=ROTATION_TOLERANCE,
                )
            )
        self.assertEqual(len(messages), 16)
        self.assertEqual(len({message.address for message in messages}), 16)
        self.assertEqual(
            sum(message.address.endswith("/position") for message in messages), 8
        )
        self.assertEqual(
            sum(message.address.endswith("/rotation") for message in messages), 8
        )
        self.assertEqual(
            tuple(item.address for item in decoded),
            tuple(item.address for item in messages),
        )
        for original, recovered in zip(messages, decoded):
            for actual, expected in zip(recovered.values, original.values):
                self.assertAlmostEqual(actual, expected, delta=FLOAT32_TOLERANCE)


if __name__ == "__main__":
    unittest.main()
