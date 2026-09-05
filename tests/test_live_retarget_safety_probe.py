"""Offline tests for the research-only Phase 2E safety probe."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
from io import StringIO
import json
import math
from pathlib import Path
import threading
import time
import unittest

from research.live_retarget_safety_probe import (
    AbortReason,
    LiveRetargetSafetyProbe,
    ProbeConfig,
    _parse_args,
    execute_probe,
)


IDENTITY_POSE = ((1.0, 0.0, 0.0, 0.0),) * 24
VALID_ROOT = (0.0, 1.0, 0.0)


class ManualClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, amount: float) -> None:
        self.value += amount


class FakeCoordinateType:
    UnityCoordinate = object()


class FakeSdk:
    def __init__(
        self,
        owner: "FakeSdkModule",
        *,
        coordinate_type: object,
        use_global_rotation: bool,
    ) -> None:
        self.owner = owner
        self.coordinate_type = coordinate_type
        self.use_global_rotation = use_global_rotation
        self.pose_callback = None
        self.close_callback = None

    def set_pose_msg_callback(self, callback) -> None:
        self.owner.pose_callback_registrations += 1
        self.pose_callback = callback

    def set_exception_close_callback(self, callback) -> None:
        self.owner.close_callback_registrations += 1
        self.close_callback = callback

    def open(self, port: int) -> int:
        self.owner.open_calls += 1
        self.owner.last_port = port
        return self.owner.open_result

    def close(self) -> None:
        self.owner.close_calls += 1
        if self.owner.close_raises:
            raise RuntimeError("fixed fake close failure")
        if self.owner.callback_during_intentional_close and self.close_callback:
            self.close_callback(self)

    def emit_pose(
        self,
        trans=VALID_ROOT,
        pose24=IDENTITY_POSE,
        static_index=-1,
        timestamp=1.0,
    ) -> None:
        if self.pose_callback is None:
            raise AssertionError("Pose callback was not registered")
        self.pose_callback(self, trans, pose24, static_index, timestamp)

    def emit_abnormal_close(self) -> None:
        if self.close_callback is None:
            raise AssertionError("Close callback was not registered")
        self.close_callback(self)


class FakeSdkModule:
    CoordinateType = FakeCoordinateType

    def __init__(self, *, open_result: int = 0) -> None:
        self.open_result = open_result
        self.constructor_calls = 0
        self.pose_callback_registrations = 0
        self.close_callback_registrations = 0
        self.open_calls = 0
        self.close_calls = 0
        self.close_raises = False
        self.callback_during_intentional_close = False
        self.last_port = None
        self.instance = None

    def RebocapWsSdk(
        self, *, coordinate_type: object, use_global_rotation: bool
    ) -> FakeSdk:
        self.constructor_calls += 1
        self.instance = FakeSdk(
            self,
            coordinate_type=coordinate_type,
            use_global_rotation=use_global_rotation,
        )
        return self.instance


class TwoPosePerConsumerWait:
    def __init__(self, module: FakeSdkModule, clock: ManualClock) -> None:
        self.module = module
        self.clock = clock
        self.source_timestamp = 1000.0

    def __call__(self, _event: threading.Event, timeout: float) -> None:
        for _ in range(2):
            step = timeout * 0.5
            self.clock.advance(step)
            self.source_timestamp += step
            self.module.instance.emit_pose(timestamp=self.source_timestamp)


class ProbeConfigAndCliTests(unittest.TestCase):
    def test_defaults_and_duration_bounds(self):
        config = ProbeConfig()
        self.assertEqual(config.duration_seconds, 20.0)
        self.assertEqual(config.stale_after_seconds, 0.250)
        self.assertEqual(config.quaternion_norm_tolerance, 1e-4)
        self.assertEqual(config.consumer_hz, 30.0)
        self.assertEqual(config.pure_pipeline_p99_budget_ms, 10.0)
        for duration in (0.999, 60.001, math.nan, math.inf, False, True):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    ProbeConfig(duration_seconds=duration)
        self.assertEqual(ProbeConfig(duration_seconds=1).duration_seconds, 1.0)
        self.assertEqual(ProbeConfig(duration_seconds=60).duration_seconds, 60.0)

    def test_cli_requires_external_path_port_and_process_id(self):
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                _parse_args([])
        args = _parse_args(
            [
                "--sdk-root",
                "external-sdk",
                "--port",
                "7690",
                "--process-id",
                "123",
            ]
        )
        self.assertEqual(args.sdk_root, Path("external-sdk"))
        self.assertEqual(args.port, 7690)
        self.assertEqual(args.process_id, 123)
        self.assertEqual(args.config, ProbeConfig())


class ProbeValuePathTests(unittest.TestCase):
    def test_fake_sdk_run_is_one_client_latest_only_and_full_memory_pipeline(self):
        clock = ManualClock()
        sdk_module = FakeSdkModule()
        waiter = TwoPosePerConsumerWait(sdk_module, clock)
        report = execute_probe(
            sdk_module,
            port=7690,
            process_id=123,
            config=ProbeConfig(duration_seconds=2.0),
            clock=clock,
            waiter=waiter,
            process_guard=lambda _pid: True,
        )

        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(sdk_module.constructor_calls, 1)
        self.assertEqual(sdk_module.pose_callback_registrations, 1)
        self.assertEqual(sdk_module.close_callback_registrations, 1)
        self.assertEqual(sdk_module.open_calls, 1)
        self.assertEqual(sdk_module.close_calls, 1)
        self.assertIs(
            sdk_module.instance.coordinate_type,
            FakeCoordinateType.UnityCoordinate,
        )
        self.assertTrue(sdk_module.instance.use_global_rotation)
        counts = report["counts"]
        self.assertGreaterEqual(counts["publish_accepted"], 100)
        self.assertEqual(
            counts["slot_replacements_total"],
            counts["publish_accepted"] - 1,
        )
        self.assertEqual(counts["latest_sequence"], counts["publish_accepted"])
        self.assertGreater(counts["unseen_replacements_before_snapshot"], 0)
        self.assertEqual(
            counts["unseen_replacements_before_snapshot"],
            counts["sequence_gap_drops"],
        )
        self.assertGreater(counts["sequence_gap_drops"], 0)
        self.assertEqual(
            counts["decoded_messages"],
            counts["processed_unique_sequences"] * 16,
        )
        self.assertEqual(
            counts["pipeline_successes"], counts["processed_unique_sequences"]
        )
        self.assertEqual(report["callback_rate"]["average_hz"], 60.0)
        self.assertEqual(report["validation"]["expected_joint_count"], 24)
        self.assertEqual(report["validation"]["adapter_errors"], 0)
        self.assertEqual(report["cadence_thresholds_ms"]["receive_gap"], [50.0, 100.0, 250.0])
        self.assertEqual(report["cadence_thresholds_ms"]["receive_burst_less_than"], 4.0)
        self.assertTrue(report["invalidation"]["controlled_stale_clear"])
        self.assertTrue(report["invalidation"]["final_disconnected_clear"])
        self.assertFalse(report["invalidation"]["latest_sample_present"])
        self.assertEqual(report["lifecycle"]["natural_disconnect"], "NOT_TRIGGERED")
        self.assertEqual(
            report["lifecycle"]["external_disconnect_evidence"],
            "UNVERIFIED / NOT OBSERVED",
        )

    def test_open_failure_closes_once_and_never_retries(self):
        clock = ManualClock()
        sdk_module = FakeSdkModule(open_result=7)
        report = execute_probe(
            sdk_module,
            port=7690,
            process_id=123,
            config=ProbeConfig(duration_seconds=1.0),
            clock=clock,
            waiter=lambda _event, _timeout: None,
            process_guard=lambda _pid: True,
        )
        self.assertEqual(report["status"], "ABORTED")
        self.assertEqual(report["abort_reason"], AbortReason.SDK_OPEN_FAILED.value)
        self.assertEqual(sdk_module.constructor_calls, 1)
        self.assertEqual(sdk_module.open_calls, 1)
        self.assertEqual(sdk_module.close_calls, 1)
        self.assertEqual(report["safety"]["reconnect_attempts"], 0)

    def test_intentional_close_callback_is_not_reported_as_natural_disconnect(self):
        clock = ManualClock()
        sdk_module = FakeSdkModule()
        sdk_module.callback_during_intentional_close = True
        waiter = TwoPosePerConsumerWait(sdk_module, clock)
        report = execute_probe(
            sdk_module,
            port=7690,
            process_id=123,
            config=ProbeConfig(duration_seconds=2.0),
            clock=clock,
            waiter=waiter,
            process_guard=lambda _pid: True,
        )
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["lifecycle"]["natural_disconnect"], "NOT_TRIGGERED")


class CallbackAbortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = ManualClock(1.0)

    def new_probe(self) -> LiveRetargetSafetyProbe:
        return LiveRetargetSafetyProbe(
            ProbeConfig(duration_seconds=1.0), clock=self.clock
        )

    def assert_invalid(self, callback_args, reason: AbortReason) -> None:
        probe = self.new_probe()
        probe.on_pose(None, *callback_args)
        report = probe.aggregate_result()
        self.assertEqual(report["status"], "ABORTED")
        self.assertEqual(report["abort_reason"], reason.value)
        self.assertEqual(report["counts"]["invalid_callbacks"], 1)
        self.assertFalse(report["invalidation"]["latest_sample_present"])

    def test_root_and_pose_count_validation_abort_first(self):
        self.assert_invalid(
            ((0.0, 1.0), IDENTITY_POSE, -1, 1.0),
            AbortReason.INVALID_ROOT_TRANSLATION,
        )
        self.assert_invalid(
            ((0.0, math.nan, 0.0), IDENTITY_POSE, -1, 1.0),
            AbortReason.INVALID_ROOT_TRANSLATION,
        )
        self.assert_invalid(
            (VALID_ROOT, IDENTITY_POSE[:-1], -1, 1.0),
            AbortReason.INVALID_POSE_COUNT,
        )

    def test_quaternion_shape_finite_and_raw_norm_validation_abort(self):
        malformed = list(IDENTITY_POSE)
        malformed[0] = (1.0, 0.0, 0.0)
        self.assert_invalid(
            (VALID_ROOT, malformed, -1, 1.0), AbortReason.INVALID_QUATERNION
        )
        nonfinite = list(IDENTITY_POSE)
        nonfinite[0] = (1.0, math.inf, 0.0, 0.0)
        self.assert_invalid(
            (VALID_ROOT, nonfinite, -1, 1.0), AbortReason.INVALID_QUATERNION
        )
        nonunit = list(IDENTITY_POSE)
        nonunit[0] = (1.001, 0.0, 0.0, 0.0)
        self.assert_invalid(
            (VALID_ROOT, nonunit, -1, 1.0),
            AbortReason.INVALID_QUATERNION_NORM,
        )

    def test_nonfinite_source_timestamp_aborts(self):
        self.assert_invalid(
            (VALID_ROOT, IDENTITY_POSE, -1, math.nan),
            AbortReason.INVALID_SOURCE_TIMESTAMP,
        )

    def test_equal_receive_and_source_order_each_abort_without_old_sample(self):
        receive_probe = self.new_probe()
        receive_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 10.0)
        receive_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 11.0)
        receive_report = receive_probe.aggregate_result()
        self.assertEqual(
            receive_report["abort_reason"], AbortReason.RECEIVE_TIMESTAMP_ORDER.value
        )
        self.assertEqual(receive_report["counts"]["receive_order_rejections"], 1)
        self.assertFalse(receive_report["invalidation"]["latest_sample_present"])

        source_probe = self.new_probe()
        source_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 10.0)
        self.clock.advance(0.01)
        source_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 10.0)
        source_report = source_probe.aggregate_result()
        self.assertEqual(
            source_report["abort_reason"], AbortReason.SOURCE_TIMESTAMP_ORDER.value
        )
        self.assertEqual(source_report["counts"]["source_order_rejections"], 1)
        self.assertFalse(source_report["invalidation"]["latest_sample_present"])

    def test_receive_gap_and_followed_burst_are_counted_without_waking_consumer(self):
        probe = self.new_probe()
        probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.0)
        self.assertFalse(probe.wake.is_set())
        self.clock.advance(0.060)
        probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.060)
        self.clock.advance(0.001)
        probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.061)

        counts = probe.aggregate_result()["counts"]
        self.assertEqual(counts["receive_gaps_ge_50ms"], 1)
        self.assertEqual(counts["receive_gaps_ge_100ms"], 0)
        self.assertEqual(counts["receive_bursts_lt_4ms"], 1)
        self.assertEqual(counts["gap_followed_burst_candidates"], 1)
        self.assertEqual(counts["source_jumps_ge_250ms"], 0)

    def test_stale_abnormal_close_and_late_callback_all_clear(self):
        stale_probe = self.new_probe()
        stale_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.0)
        self.clock.advance(0.250000001)
        stale_probe.process_latest()
        stale_report = stale_probe.aggregate_result()
        self.assertEqual(
            stale_report["abort_reason"], AbortReason.STALE_LATEST_POSE.value
        )
        self.assertFalse(stale_report["invalidation"]["latest_sample_present"])
        stale_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 2.0)
        self.assertEqual(
            stale_probe.aggregate_result()["counts"]["late_callbacks_rejected"], 1
        )

        close_probe = self.new_probe()
        close_probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 1.0)
        close_probe.on_sdk_close(None)
        close_report = close_probe.aggregate_result()
        self.assertEqual(
            close_report["abort_reason"], AbortReason.SDK_ABNORMAL_CLOSE.value
        )
        self.assertEqual(close_report["lifecycle"]["natural_disconnect"], "TRIGGERED")
        self.assertFalse(close_report["invalidation"]["latest_sample_present"])


class DurationPrivacyAndBoundaryTests(unittest.TestCase):
    def test_sixty_second_boundary_closes_without_extending(self):
        clock = ManualClock()
        sdk_module = FakeSdkModule()

        def advance_only(_event: threading.Event, timeout: float) -> None:
            clock.advance(timeout)

        report = execute_probe(
            sdk_module,
            port=7690,
            process_id=123,
            config=ProbeConfig(duration_seconds=60.0),
            clock=clock,
            waiter=advance_only,
            process_guard=lambda _pid: True,
        )
        self.assertEqual(report["status"], "UNVERIFIED")
        self.assertEqual(report["lifecycle"]["observation_duration_seconds"], 60.0)
        self.assertEqual(sdk_module.open_calls, 1)
        self.assertEqual(sdk_module.close_calls, 1)
        self.assertNotIn("SIXTY_SECOND_MAXIMUM", report["acceptance_failed"])

    def test_process_guard_failure_never_constructs_or_opens_client(self):
        sdk_module = FakeSdkModule()
        report = execute_probe(
            sdk_module,
            port=54321,
            process_id=123,
            config=ProbeConfig(duration_seconds=1.0),
            process_guard=lambda _pid: False,
        )
        self.assertEqual(report["status"], "ABORTED")
        self.assertEqual(report["abort_reason"], AbortReason.PROCESS_NOT_ALIVE.value)
        self.assertEqual(sdk_module.constructor_calls, 0)
        self.assertEqual(sdk_module.open_calls, 0)
        self.assertEqual(sdk_module.close_calls, 0)

    def test_aggregate_contains_no_raw_values_bytes_path_or_endpoint(self):
        clock = ManualClock()
        sdk_module = FakeSdkModule()
        waiter = TwoPosePerConsumerWait(sdk_module, clock)
        report = execute_probe(
            sdk_module,
            port=54321,
            process_id=98765,
            config=ProbeConfig(duration_seconds=2.0),
            clock=clock,
            waiter=waiter,
            process_guard=lambda _pid: True,
        )
        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("54321", encoded)
        self.assertNotIn("98765", encoded)
        self.assertNotIn("external-sdk", encoded)
        self.assertNotIn("1000.0", encoded)
        self.assertNotIn("1.0, 0.0, 0.0, 0.0", encoded)
        self.assertEqual(report["safety"]["raw_pose_frames_persisted"], 0)
        self.assertEqual(report["safety"]["raw_time_series_persisted"], 0)
        self.assertEqual(report["safety"]["message_bytes_persisted"], 0)
        self.assertEqual(report["safety"]["direct_transport_sends"], 0)
        self.assertEqual(report["safety"]["application_process_setting_changes"], 0)

    def test_research_source_has_no_transport_or_file_write_api(self):
        source_path = (
            Path(__file__).resolve().parents[1]
            / "research"
            / "live_retarget_safety_probe.py"
        )
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_module = "sock" + "et"
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn(forbidden_module, imported)
        forbidden_attributes = {
            "send",
            "sendto",
            "write_text",
            "write_bytes",
            "replace",
        }
        used_attributes = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        self.assertTrue(forbidden_attributes.isdisjoint(used_attributes))
        builtin_file_opens = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ]
        self.assertEqual(builtin_file_opens, [])


class RecoveryClockAndProgressTests(unittest.TestCase):
    def test_both_default_clocks_are_the_same_high_resolution_clock(self):
        self.assertIs(LiveRetargetSafetyProbe.__init__.__kwdefaults__["clock"], time.perf_counter)
        self.assertIs(execute_probe.__kwdefaults__["clock"], time.perf_counter)

    def test_coarse_clock_reproduces_false_tie_without_fabricated_timestamps(self):
        precise = ManualClock(1.0)
        coarse = lambda: math.floor(precise() * 64.0) / 64.0
        old_probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=coarse)
        fixed_probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=precise)
        for sequence in range(120):
            precise.advance(1.0 / 120.0)
            for probe in (old_probe, fixed_probe):
                probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, sequence / 120.0)
        self.assertEqual(old_probe.abort_reason, AbortReason.RECEIVE_TIMESTAMP_ORDER)
        self.assertEqual(fixed_probe.abort_reason, AbortReason.NONE)
        self.assertEqual(fixed_probe.aggregate_result()["counts"]["publish_accepted"], 120)

    def test_synthetic_rates_and_one_second_consumer_stall_keep_only_latest(self):
        for producer_hz in (60, 120):
            with self.subTest(producer_hz=producer_hz):
                clock = ManualClock(1.0)
                probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=clock)
                for sequence in range(1, producer_hz + 1):
                    clock.advance(1.0 / producer_hz)
                    probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, sequence / producer_hz)
                # The consumer has been absent for a whole second, but the last
                # producer value is fresh. No backlog may be replayed on return.
                probe.process_latest()
                probe.process_latest()
                report = probe.aggregate_result()
                self.assertEqual(report["abort_reason"], "NONE")
                self.assertEqual(report["counts"]["publish_accepted"], producer_hz)
                self.assertEqual(report["counts"]["processed_unique_sequences"], 1)
                self.assertEqual(report["counts"]["sequence_gap_drops"], producer_hz - 1)

    def test_real_thread_60hz_120hz_and_burst_with_consumer_stall(self):
        # This is an ordering/handoff test, not an OS scheduling benchmark.
        for producer_hz, frame_count in ((60, 12), (120, 24), (None, 120)):
            with self.subTest(producer_hz=producer_hz):
                probe = LiveRetargetSafetyProbe(ProbeConfig(stale_after_seconds=2.0))
                done, cancelled = threading.Event(), threading.Event()

                def producer():
                    try:
                        started = time.perf_counter()
                        for sequence in range(frame_count):
                            if cancelled.is_set():
                                return
                            if producer_hz is not None:
                                cancelled.wait(max(0.0, started + sequence / producer_hz - time.perf_counter()))
                            probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, sequence / 120.0)
                    finally:
                        done.set()

                worker = threading.Thread(target=producer, daemon=True)
                worker.start()
                try:
                    cancelled.wait(0.080)  # Producer keeps replacing while consumer stalls.
                    deadline = time.perf_counter() + 3.0
                    while not done.is_set() and time.perf_counter() < deadline:
                        probe.process_latest()
                        done.wait(1.0 / 30.0)
                    worker.join(timeout=0.5)
                    self.assertFalse(worker.is_alive())
                    probe.process_latest()
                    report = probe.aggregate_result()
                    self.assertEqual(report["abort_reason"], "NONE")
                    self.assertEqual(report["counts"]["publish_accepted"], frame_count)
                    self.assertEqual(report["counts"]["receive_order_rejections"], 0)
                    self.assertEqual(report["counts"]["source_order_rejections"], 0)
                    self.assertGreater(report["counts"]["sequence_gap_drops"], 0)
                    self.assertEqual(
                        report["counts"]["processed_unique_sequences"] + report["counts"]["sequence_gap_drops"],
                        frame_count,
                    )
                finally:
                    cancelled.set()
                    worker.join(timeout=0.5)

    def test_lifecycle_heartbeat_pre_close_and_first_callback_are_aggregate_only(self):
        clock, sdk_module, events = ManualClock(), FakeSdkModule(), []
        report = execute_probe(
            sdk_module, port=54321, process_id=98765,
            config=ProbeConfig(duration_seconds=2.0), clock=clock,
            waiter=TwoPosePerConsumerWait(sdk_module, clock),
            process_guard=lambda _pid: True, progress=events.append,
        )
        self.assertEqual([event["stage"] for event in events], [
            "construct_before", "construct_after", "registration_before", "registration_after",
            "open_before", "open_after", "observe_start", "heartbeat", "pre_close",
            "close_before", "close_after", "complete",
        ])
        pre_close = next(event["aggregate"] for event in events if event["stage"] == "pre_close")
        self.assertEqual(pre_close["status"], "IN_PROGRESS")
        self.assertGreaterEqual(pre_close["counts"]["publish_accepted"], 100)
        self.assertEqual(pre_close["lifecycle"]["sdk_close_successes"], 0)
        open_before = next(event["aggregate"] for event in events if event["stage"] == "open_before")
        self.assertEqual(open_before["lifecycle"]["sdk_open_attempts"], 1)
        self.assertEqual(open_before["lifecycle"]["sdk_open_successes"], 0)
        self.assertEqual(events[-1]["aggregate"], report)
        self.assertEqual(report["status"], "PASS")
        self.assertAlmostEqual(report["lifecycle"]["first_callback_delay_seconds"], 1.0 / 60.0, places=6)
        self.assertEqual(report["lifecycle"]["last_callback_age_seconds"], 0.0)
        serialized = json.dumps(events)
        for private_value in ("54321", "98765", "1000.0", "1.0, 0.0, 0.0, 0.0"):
            self.assertNotIn(private_value, serialized)
        self.assertTrue(all(event["aggregate"]["status"] != "PASS" for event in events[:-1]))

    def test_pre_close_aggregate_is_available_while_fake_close_blocks(self):
        clock, sdk_module, events = ManualClock(), FakeSdkModule(), []
        release, closing = threading.Event(), threading.Event()
        original_constructor = sdk_module.RebocapWsSdk

        def constructor(**kwargs):
            sdk = original_constructor(**kwargs)
            original_close = sdk.close

            def blocked_close():
                closing.set()
                release.wait(3.0)
                original_close()

            sdk.close = blocked_close
            return sdk

        sdk_module.RebocapWsSdk = constructor
        reports = []
        worker = threading.Thread(target=lambda: reports.append(execute_probe(
            sdk_module, port=7690, process_id=123,
            config=ProbeConfig(duration_seconds=2.0), clock=clock,
            waiter=TwoPosePerConsumerWait(sdk_module, clock),
            process_guard=lambda _pid: True, progress=events.append,
        )), daemon=True)
        worker.start()
        try:
            self.assertTrue(closing.wait(2.0))
            self.assertEqual(reports, [])
            self.assertEqual(events[-1]["stage"], "close_before")
            self.assertEqual(events[-1]["aggregate"]["status"], "IN_PROGRESS")
            self.assertGreater(events[-1]["aggregate"]["counts"]["publish_accepted"], 100)
            self.assertEqual(events[-1]["aggregate"]["lifecycle"]["sdk_close_successes"], 0)
        finally:
            release.set()
            worker.join(timeout=2.0)
        self.assertFalse(worker.is_alive())
        self.assertEqual(reports[0]["status"], "PASS")

    def test_progress_failure_is_sanitized_and_does_not_open_client(self):
        sdk_module = FakeSdkModule()

        def broken_progress(_event):
            raise RuntimeError("private diagnostic must never escape")

        report = execute_probe(
            sdk_module, port=7690, process_id=123, config=ProbeConfig(),
            process_guard=lambda _pid: True, progress=broken_progress,
        )
        self.assertEqual(report["abort_reason"], "PROGRESS_REPORT_FAILED")
        self.assertEqual(sdk_module.constructor_calls, 0)
        self.assertEqual(sdk_module.open_calls, 0)
        self.assertNotIn("private diagnostic", json.dumps(report))

    def test_heartbeat_last_callback_age_and_no_callback_are_distinct(self):
        clock, events, sdk_module = ManualClock(), [], FakeSdkModule()
        report = execute_probe(
            sdk_module, port=7690, process_id=123, config=ProbeConfig(duration_seconds=2.0),
            clock=clock, waiter=lambda _event, timeout: clock.advance(timeout),
            process_guard=lambda _pid: True, progress=events.append,
        )
        heartbeat = next(event["aggregate"] for event in events if event["stage"] == "heartbeat")
        self.assertEqual(heartbeat["counts"]["callbacks_received"], 0)
        self.assertIsNone(heartbeat["lifecycle"]["first_callback_delay_seconds"])
        self.assertIsNone(heartbeat["lifecycle"]["last_callback_age_seconds"])
        probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=clock)
        probe.on_pose(None, VALID_ROOT, IDENTITY_POSE, -1, 10.0)
        clock.advance(0.125)
        self.assertEqual(probe.aggregate_result()["lifecycle"]["last_callback_age_seconds"], 0.125)
        self.assertEqual(report["status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
