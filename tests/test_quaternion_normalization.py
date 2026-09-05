"""Independent arithmetic checks for exact-unit reuse and finite overflow."""

from dataclasses import FrozenInstanceError
import math
import random
import unittest

from reboretarget import Quaternion


def components(rotation):
    return (rotation.w, rotation.x, rotation.y, rotation.z)


def original_normalization(values):
    """The original arithmetic, independent of the implementation under test."""
    w, x, y, z = values
    magnitude = math.sqrt(w * w + x * x + y * y + z * z)
    if magnitude <= 1e-12:
        raise ValueError("zero magnitude")
    return tuple(value / magnitude for value in values)


class QuaternionNormalizationTests(unittest.TestCase):
    def test_exact_unit_reuses_immutable_value(self):
        for values in ((1., 0., 0., 0.), (-1., -0., 0., 0.), (.5, .5, .5, .5)):
            with self.subTest(values=values):
                rotation = Quaternion(*values)
                self.assertIs(rotation.normalized(), rotation)
                with self.assertRaises(FrozenInstanceError):
                    rotation.w = 0.

    def test_seeded_nonunit_values_match_original_arithmetic_exactly(self):
        generator = random.Random(205)
        for _ in range(500):
            values = tuple(generator.uniform(-1e6, 1e6) for _ in range(4))
            for signed in (values, tuple(-value for value in values)):
                actual = components(Quaternion(*signed).normalized())
                self.assertEqual(actual, original_normalization(signed))
                self.assertAlmostEqual(math.sqrt(sum(value * value for value in actual)), 1.)

    def test_near_unit_is_not_an_epsilon_shortcut(self):
        for length in (1. - 2**-52, 1. + 2**-52, 1. - 1e-10, 1. + 1e-10):
            with self.subTest(length=length):
                rotation = Quaternion(length, 0., 0., 0.)
                normalized = rotation.normalized()
                self.assertIsNot(normalized, rotation)
                self.assertEqual(components(normalized), original_normalization(components(rotation)))

    def test_rotation_boundaries_and_signs_match_original(self):
        for angle in (0., 30., 89.9, 90., 90.1, 179., 180., 181., -179.):
            half_angle = math.radians(angle) / 2
            for axis in range(3):
                values = [math.cos(half_angle), 0., 0., 0.]
                values[axis + 1] = math.sin(half_angle)
                for sign in (1., -1.):
                    signed = tuple(sign * value for value in values)
                    self.assertEqual(components(Quaternion(*signed).normalized()), original_normalization(signed))

    def test_nonfinite_components_are_still_rejected(self):
        for invalid in (math.nan, math.inf, -math.inf):
            for index in range(4):
                values = [1., 0., 0., 0.]
                values[index] = invalid
                with self.assertRaises(ValueError):
                    Quaternion(*values)

    def test_zero_and_near_zero_are_still_rejected(self):
        for length in (0., 1e-300, 1e-13, 1e-12):
            with self.subTest(length=length), self.assertRaises(ValueError):
                Quaternion(length, 0., 0., 0.).normalized()
        self.assertEqual(components(Quaternion(1.01e-12, 0., 0., 0.).normalized()), (1., 0., 0., 0.))

    def test_finite_overflow_does_not_collapse_to_zero(self):
        for values in ((1e308, 0., 0., 0.), (1e308, -1e308, 1e308, -1e308),
                       (1e200, -2e200, 3e200, -4e200)):
            scale = max(abs(value) for value in values)
            scaled = tuple(value / scale for value in values)
            expected = original_normalization(scaled)
            positive = components(Quaternion(*values).normalized())
            negative = components(Quaternion(*(-value for value in values)).normalized())
            self.assertEqual(positive, expected)
            self.assertEqual(negative, tuple(-value for value in positive))
            self.assertTrue(all(math.isfinite(value) for value in positive))
            self.assertAlmostEqual(sum(value * value for value in positive), 1.)


if __name__ == "__main__":
    unittest.main()
