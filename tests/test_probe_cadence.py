"""Deterministic wake/deadline invariants, not OS microsecond thresholds."""
import threading
import unittest
from unittest.mock import patch

from research.live_retarget_safety_probe import LiveRetargetSafetyProbe, ProbeConfig, execute_probe
from tests.test_live_retarget_safety_probe import FakeSdkModule, ManualClock, VALID_ROOT, IDENTITY_POSE


class ProbeCadenceTests(unittest.TestCase):
    def test_normal_publish_wakes_consumer_and_burst_coalesces(self):
        clock = ManualClock(1.)
        probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=clock)
        self.assertFalse(probe.wake.is_set())
        for sequence in range(1, 31):
            clock.advance(.001)
            probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, sequence / 60)
        self.assertTrue(probe.wake.is_set())
        probe.wake.clear()
        probe.process_latest()
        probe.process_latest()
        counts = probe.aggregate_result()["counts"]
        self.assertEqual(counts["processed_unique_sequences"], 1)
        self.assertEqual(counts["sequence_gap_drops"], 29)

    def test_work_time_is_inside_period_and_early_wakes_do_not_bypass_ceiling(self):
        clock, sdk, starts, waits = ManualClock(), FakeSdkModule(), [], []
        stop = threading.Event()
        sequence = 0
        original = LiveRetargetSafetyProbe.process_latest

        def processing(probe):
            starts.append(clock())
            original(probe)
            clock.advance(.010)  # deterministic work, not a real sleep
            if len(starts) >= 6:
                stop.set()

        def wait(event, timeout):
            nonlocal sequence
            waits.append(timeout)
            # New callbacks can arrive before the next eligible start.
            clock.advance(min(.005, timeout))
            sequence += 1
            sdk.instance.emit_pose(timestamp=sequence / 60.)

        with patch.object(LiveRetargetSafetyProbe, "process_latest", processing):
            report = execute_probe(sdk, port=7690, process_id=1,
                config=ProbeConfig(duration_seconds=2., consumer_hz=30),
                clock=clock, waiter=wait, process_guard=lambda _: True, stop_event=stop)
        self.assertEqual(report["abort_reason"], "USER_STOP")
        self.assertEqual(sdk.close_calls, 1)
        self.assertAlmostEqual(waits[0], 1/30 - .010)
        for left, right in zip(starts, starts[1:]):
            self.assertAlmostEqual(right-left, 1/30)
        self.assertLess(len(waits), 40)

    def test_arrival_during_processing_remains_signaled_for_next_snapshot(self):
        clock = ManualClock(1.)
        probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=clock)
        probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.)
        probe.wake.clear()
        original = probe.slot.snapshot_at

        def snapshot(slot, now):
            result = original(now)
            clock.advance(.001)
            probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 2.)
            return result

        with patch.object(type(probe.slot), "snapshot_at", snapshot):
            probe.process_latest()
        self.assertTrue(probe.wake.is_set())
        probe.wake.clear()
        probe.process_latest()
        self.assertEqual(probe.aggregate_result()["counts"]["processed_unique_sequences"], 2)

    def test_late_wake_keeps_phase_and_skips_missed_deadlines_without_catchup(self):
        for overshoot, spacing in ((.005, 1/30), (.110, 4/30)):
            clock, sdk, starts, stop = ManualClock(), FakeSdkModule(), [], threading.Event()
            original = LiveRetargetSafetyProbe.process_latest
            def process(probe):
                starts.append(clock())
                original(probe)
                clock.advance(.002)
                if len(starts) == 4:
                    stop.set()
            def wait(_event, timeout):
                clock.advance(timeout + overshoot)
            with patch.object(LiveRetargetSafetyProbe, "process_latest", process):
                execute_probe(sdk, port=7690, process_id=1,
                    config=ProbeConfig(duration_seconds=2), clock=clock,
                    waiter=wait, process_guard=lambda _: True, stop_event=stop)
            self.assertEqual(len(starts), 4)
            self.assertAlmostEqual(starts[1], 1/30 + overshoot)
            for left, right in zip(starts[1:], starts[2:]):
                self.assertAlmostEqual(right-left, spacing)
            self.assertEqual(sdk.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
