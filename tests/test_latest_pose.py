import gc
import math
import threading
import unittest
import weakref
from dataclasses import FrozenInstanceError

from reboretarget.latest_pose import (
    LatestPoseSample,
    LatestPoseSlot,
    LatestPoseSnapshot,
    LatestPoseState,
    PublishResult,
)


STALE_AFTER_SECONDS = 0.250


class _WeakPayload:
    pass


class LatestPoseContractTests(unittest.TestCase):
    def test_initial_state_and_positive_finite_threshold(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        self.assertEqual(slot.stale_after_seconds, STALE_AFTER_SECONDS)
        self.assertEqual(
            slot.snapshot_at(0.0),
            LatestPoseSnapshot(LatestPoseState.EMPTY, None),
        )
        for invalid in (0.0, -0.001, math.nan, math.inf, -math.inf, False, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    LatestPoseSlot[str](invalid)

    def test_first_publish_preserves_opaque_payload_identity(self):
        slot = LatestPoseSlot[object](STALE_AFTER_SECONDS)
        payload = object()
        result = slot.publish(
            payload,
            receive_monotonic=1.0,
            source_timestamp=-10.0,
        )
        snapshot = slot.snapshot_at(1.0)
        self.assertIs(result, PublishResult.ACCEPTED)
        self.assertIs(snapshot.state, LatestPoseState.VALID)
        self.assertIs(snapshot.sample.value, payload)
        self.assertEqual(snapshot.sample.sequence, 1)
        self.assertEqual(snapshot.sample.receive_monotonic, 1.0)
        self.assertEqual(snapshot.sample.source_timestamp, -10.0)

        self.assertIs(
            slot.publish(None, receive_monotonic=2.0, source_timestamp=-9.0),
            PublishResult.ACCEPTED,
        )
        none_snapshot = slot.snapshot_at(2.0)
        self.assertIsNotNone(none_snapshot.sample)
        self.assertIsNone(none_snapshot.sample.value)

    def test_newer_publish_overwrites_the_only_sample(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("old", receive_monotonic=1.0, source_timestamp=10.0)
        result = slot.publish("new", receive_monotonic=2.0, source_timestamp=11.0)
        snapshot = slot.snapshot_at(2.0)
        self.assertIs(result, PublishResult.ACCEPTED)
        self.assertEqual(snapshot.sample.value, "new")
        self.assertEqual(snapshot.sample.sequence, 2)

    def test_receive_equal_or_regression_rejects_first_and_changes_nothing(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("kept", receive_monotonic=2.0, source_timestamp=20.0)
        expected = slot.snapshot_at(2.0)
        cases = (
            (2.0, 21.0),
            (1.0, 19.0),
        )
        for receive, source in cases:
            with self.subTest(receive=receive, source=source):
                self.assertIs(
                    slot.publish(
                        "rejected",
                        receive_monotonic=receive,
                        source_timestamp=source,
                    ),
                    PublishResult.REJECTED_RECEIVE_ORDER,
                )
                self.assertEqual(slot.snapshot_at(2.0), expected)

    def test_source_equal_or_regression_rejects_and_changes_nothing(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("kept", receive_monotonic=2.0, source_timestamp=20.0)
        expected = slot.snapshot_at(2.0)
        for receive, source in ((3.0, 20.0), (4.0, 19.0)):
            with self.subTest(receive=receive, source=source):
                self.assertIs(
                    slot.publish(
                        "rejected",
                        receive_monotonic=receive,
                        source_timestamp=source,
                    ),
                    PublishResult.REJECTED_SOURCE_ORDER,
                )
                self.assertEqual(slot.snapshot_at(2.0), expected)

    def test_invalid_publish_timestamps_raise_without_advancing_sequence(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        invalid_cases = (
            (-0.001, 1.0),
            (math.nan, 1.0),
            (math.inf, 1.0),
            (False, 1.0),
            (True, 1.0),
            (1.0, math.nan),
            (1.0, math.inf),
            (1.0, -math.inf),
            (1.0, False),
            (1.0, True),
        )
        for receive, source in invalid_cases:
            with self.subTest(receive=receive, source=source):
                with self.assertRaises(ValueError):
                    slot.publish(
                        "invalid",
                        receive_monotonic=receive,
                        source_timestamp=source,
                    )
        self.assertIs(
            slot.publish("first", receive_monotonic=1.0, source_timestamp=1.0),
            PublishResult.ACCEPTED,
        )
        self.assertEqual(slot.snapshot_at(1.0).sample.sequence, 1)

    def test_invalid_snapshot_timestamp_does_not_change_state(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("kept", receive_monotonic=1.0, source_timestamp=1.0)
        for invalid in (-0.001, math.nan, math.inf, -math.inf, False, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    slot.snapshot_at(invalid)
        self.assertEqual(slot.snapshot_at(1.0).sample.value, "kept")

    def test_stale_threshold_is_strict_and_cross_thread_now_can_be_earlier(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("current", receive_monotonic=10.0, source_timestamp=1.0)
        self.assertIs(slot.snapshot_at(9.0).state, LatestPoseState.VALID)
        self.assertIs(slot.snapshot_at(10.250).state, LatestPoseState.VALID)
        stale = slot.snapshot_at(10.250000001)
        self.assertIs(stale.state, LatestPoseState.STALE)
        self.assertIsNone(stale.sample)

    def test_mark_stale_clears_sample_and_is_idempotent(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("old", receive_monotonic=1.0, source_timestamp=1.0)
        slot.mark_stale()
        slot.mark_stale()
        self.assertEqual(
            slot.snapshot_at(1.0),
            LatestPoseSnapshot(LatestPoseState.STALE, None),
        )

    def test_disconnected_clears_every_state_and_dominates_stale(self):
        slots = [LatestPoseSlot[str](STALE_AFTER_SECONDS) for _ in range(4)]
        slots[1].publish("valid", receive_monotonic=1.0, source_timestamp=1.0)
        slots[2].mark_stale()
        slots[3].mark_disconnected()
        for slot in slots:
            slot.mark_disconnected()
            slot.mark_stale()
            slot.mark_disconnected()
            self.assertEqual(
                slot.snapshot_at(2.0),
                LatestPoseSnapshot(LatestPoseState.DISCONNECTED, None),
            )

    def test_inactive_publish_is_rejected_without_state_change(self):
        for inactive in (LatestPoseState.STALE, LatestPoseState.DISCONNECTED):
            with self.subTest(inactive=inactive):
                slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
                if inactive is LatestPoseState.STALE:
                    slot.mark_stale()
                else:
                    slot.mark_disconnected()
                self.assertIs(
                    slot.publish(
                        "ignored",
                        receive_monotonic=1.0,
                        source_timestamp=1.0,
                    ),
                    PublishResult.REJECTED_INACTIVE,
                )
                self.assertEqual(
                    slot.snapshot_at(1.0),
                    LatestPoseSnapshot(inactive, None),
                )

    def test_rearm_preserves_watermarks_and_sequence(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.publish("epoch-one", receive_monotonic=10.0, source_timestamp=100.0)
        slot.mark_disconnected()
        slot.rearm()
        self.assertIs(slot.snapshot_at(10.0).state, LatestPoseState.EMPTY)
        self.assertIs(
            slot.publish(
                "delayed",
                receive_monotonic=11.0,
                source_timestamp=99.0,
            ),
            PublishResult.REJECTED_SOURCE_ORDER,
        )
        self.assertIs(
            slot.publish(
                "new",
                receive_monotonic=11.0,
                source_timestamp=101.0,
            ),
            PublishResult.ACCEPTED,
        )
        self.assertEqual(slot.snapshot_at(11.0).sample.sequence, 2)

        new_epoch_slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        self.assertIs(
            new_epoch_slot.publish(
                "new epoch",
                receive_monotonic=0.0,
                source_timestamp=0.0,
            ),
            PublishResult.ACCEPTED,
        )

    def test_rearm_is_empty_idempotent_but_rejects_valid(self):
        slot = LatestPoseSlot[str](STALE_AFTER_SECONDS)
        slot.rearm()
        slot.rearm()
        self.assertIs(slot.snapshot_at(0.0).state, LatestPoseState.EMPTY)
        slot.publish("valid", receive_monotonic=0.0, source_timestamp=0.0)
        with self.assertRaises(RuntimeError):
            slot.rearm()
        self.assertEqual(slot.snapshot_at(0.0).sample.value, "valid")

    def test_sample_and_snapshot_values_are_frozen(self):
        sample = LatestPoseSample(1, "value", 1.0, 2.0)
        snapshot = LatestPoseSnapshot(LatestPoseState.VALID, sample)
        with self.assertRaises(FrozenInstanceError):
            sample.sequence = 2
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = LatestPoseState.EMPTY


class LatestPoseRateShapeTests(unittest.TestCase):
    def test_logical_60_hz_producer_to_60_hz_consumer(self):
        slot = LatestPoseSlot[int](STALE_AFTER_SECONDS)
        consumed = []
        for frame in range(60):
            timestamp = frame / 60.0
            slot.publish(
                frame,
                receive_monotonic=timestamp,
                source_timestamp=timestamp,
            )
            consumed.append(slot.snapshot_at(timestamp).sample.value)
        self.assertEqual(consumed, list(range(60)))

    def test_logical_60_hz_producer_to_30_hz_consumer(self):
        slot = LatestPoseSlot[int](STALE_AFTER_SECONDS)
        consumed = []
        for frame in range(60):
            timestamp = frame / 60.0
            slot.publish(
                frame,
                receive_monotonic=timestamp,
                source_timestamp=timestamp,
            )
            if frame % 2 == 1:
                consumed.append(slot.snapshot_at(timestamp).sample.value)
        self.assertEqual(consumed, list(range(1, 60, 2)))

    def test_logical_120_hz_burst_to_30_hz_consumer(self):
        slot = LatestPoseSlot[int](STALE_AFTER_SECONDS)
        consumed = []
        for frame in range(120):
            timestamp = frame / 120.0
            slot.publish(
                frame,
                receive_monotonic=timestamp,
                source_timestamp=timestamp,
            )
            if frame % 4 == 3:
                consumed.append(slot.snapshot_at(timestamp).sample.value)
        self.assertEqual(consumed, list(range(3, 120, 4)))

    def test_consumer_pause_exposes_only_the_latest_value(self):
        slot = LatestPoseSlot[int](STALE_AFTER_SECONDS)
        for frame in range(101):
            timestamp = frame / 1000.0
            slot.publish(
                frame,
                receive_monotonic=timestamp,
                source_timestamp=timestamp,
            )
        snapshot = slot.snapshot_at(0.100)
        self.assertEqual(snapshot.sample.value, 100)
        self.assertEqual(snapshot.sample.sequence, 101)


class LatestPoseStorageAndConcurrencyTests(unittest.TestCase):
    def test_overwrite_and_invalidation_release_payload_references(self):
        slot = LatestPoseSlot[_WeakPayload](STALE_AFTER_SECONDS)
        first = _WeakPayload()
        first_ref = weakref.ref(first)
        slot.publish(first, receive_monotonic=1.0, source_timestamp=1.0)
        del first

        second = _WeakPayload()
        second_ref = weakref.ref(second)
        slot.publish(second, receive_monotonic=2.0, source_timestamp=2.0)
        del second
        gc.collect()
        self.assertIsNone(first_ref())
        self.assertIsNotNone(second_ref())

        slot.mark_stale()
        gc.collect()
        self.assertIsNone(second_ref())

    def test_barrier_race_is_atomic_without_assuming_a_winner(self):
        slot = LatestPoseSlot[int](1000.0)
        slot.publish(0, receive_monotonic=0.0, source_timestamp=0.0)
        start = threading.Barrier(2)
        finish = threading.Barrier(2)
        observed_sequences = []
        iterations = 200

        def producer():
            for index in range(1, iterations + 1):
                start.wait()
                slot.publish(
                    index,
                    receive_monotonic=float(index),
                    source_timestamp=float(index),
                )
                finish.wait()

        def consumer():
            for index in range(1, iterations + 1):
                start.wait()
                snapshot = slot.snapshot_at(float(index))
                observed_sequences.append(snapshot.sample.sequence)
                finish.wait()

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)
        producer_thread.start()
        consumer_thread.start()
        producer_thread.join()
        consumer_thread.join()

        self.assertEqual(len(observed_sequences), iterations)
        for index, sequence in enumerate(observed_sequences, start=1):
            self.assertIn(sequence, (index, index + 1))
        self.assertEqual(slot.snapshot_at(float(iterations)).sample.sequence, iterations + 1)


if __name__ == "__main__":
    unittest.main()
