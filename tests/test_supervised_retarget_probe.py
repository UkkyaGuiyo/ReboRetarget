"""Real spawned fake-SDK tests; no vendor SDK, sockets, or application changes."""
from __future__ import annotations

from functools import partial
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from research.live_retarget_safety_probe import LiveRetargetSafetyProbe, ProbeConfig
from research.supervised_retarget_probe import _clean_packet, supervise_probe


class SyntheticSdk:
    def __init__(self, mode, **options):
        assert options["use_global_rotation"] is True
        assert options["coordinate_type"] == "synthetic_unity"
        self.mode, self.stop = mode, threading.Event()
        self.thread = None
        if mode == "constructor_hang":
            time.sleep(3600)

    def set_pose_msg_callback(self, callback):
        self.callback = callback

    def set_exception_close_callback(self, callback):
        self.close_callback = callback

    def open(self, port):
        assert port == 7690
        if self.mode == "open_hang":
            time.sleep(3600)
        if self.mode in ("success", "burst", "malformed", "close_hang", "exit_hang"):
            def producer():
                sequence = 0
                while not self.stop.is_set():
                    for _ in range(4 if self.mode == "burst" else 1):
                        pose = ((1.0, 0.0, 0.0, 0.0),) * (23 if self.mode == "malformed" else 24)
                        self.callback(self, (0.0, 1.0, 0.0), pose, -1, sequence / 60.0)
                        sequence += 1
                    self.stop.wait(1 / 60)
            self.thread = threading.Thread(target=producer, daemon=True)
            self.thread.start()
        return 0

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(0.3)
        if self.mode == "close_hang":
            time.sleep(3600)
        if self.mode == "exit_hang":
            threading.Thread(target=lambda: time.sleep(3600), daemon=False).start()


def synthetic_loader(sdk_root, *, mode):
    # Prove child never forwards Python or native third-party diagnostics.
    print("SYNTHETIC_PRIVATE_DIAGNOSTIC_DO_NOT_FORWARD", flush=True)
    os.write(2, b"SYNTHETIC_PRIVATE_DIAGNOSTIC_DO_NOT_FORWARD\n")
    if mode == "import_hang":
        time.sleep(3600)
    return SimpleNamespace(
        CoordinateType=SimpleNamespace(UnityCoordinate="synthetic_unity"),
        RebocapWsSdk=partial(SyntheticSdk, mode),
    )


class SupervisorTests(unittest.TestCase):
    def run_fake(self, mode):
        config = ProbeConfig(duration_seconds=1, stale_after_seconds=1,
            minimum_callbacks=20, minimum_callback_hz=30, maximum_callback_hz=90,
            pure_pipeline_p99_budget_ms=100)
        started = time.perf_counter()
        report = supervise_probe(sdk_root=Path(__file__).parent, port=7690,
            process_id=os.getpid(), config=config, hard_timeout_seconds=3.5,
            _sdk_loader=partial(synthetic_loader, mode=mode))
        self.assertLess(time.perf_counter() - started, 3.5)
        self.assertTrue(report["within_deadline"])
        self.assertTrue(report["child_exit_observed"])
        self.assertNotEqual(report["child_pid"], os.getpid())
        self.assertEqual(report["reconnect_attempts"], 0)
        self.assertNotIn("SYNTHETIC_PRIVATE", json.dumps(report))
        self.assertNotIn(str(Path(__file__).resolve()), json.dumps(report))
        return report

    def test_spawned_import_hang_is_bounded(self):
        report = self.run_fake("import_hang")
        self.assertEqual(report["latest_checkpoint"]["stage"], "import_before")
        self.assertTrue(report["termination_requested"])
        self.assertIsNone(report["aggregate"])

    def test_spawned_constructor_hang_is_bounded(self):
        report = self.run_fake("constructor_hang")
        self.assertEqual(report["latest_checkpoint"]["stage"], "construct_before")
        self.assertTrue(report["termination_requested"])

    def test_spawned_open_hang_preserves_partial_aggregate(self):
        report = self.run_fake("open_hang")
        self.assertEqual(report["latest_checkpoint"]["stage"], "open_before")
        self.assertTrue(report["termination_requested"])
        self.assertEqual(report["aggregate"]["counts"]["callbacks_received"], 0)
        self.assertFalse(report["result_ready"])

    def test_spawned_close_hang_preserves_callback_evidence(self):
        report = self.run_fake("close_hang")
        self.assertEqual(report["latest_checkpoint"]["stage"], "close_before")
        self.assertTrue(report["termination_requested"])
        self.assertGreater(report["aggregate"]["counts"]["callbacks_received"], 20)
        self.assertEqual(report["status"], "UNVERIFIED")

    def test_spawned_success_pipeline(self):
        report = self.run_fake("success")
        self.assertTrue(report["result_ready"])
        self.assertFalse(report["termination_requested"])
        self.assertEqual(report["child_exit_code"], 0)
        self.assertGreater(report["aggregate"]["counts"]["decoded_messages"], 0)
        self.assertEqual(report["aggregate"]["abort_reason"], "NONE")
        self.assertEqual(report["aggregate"]["lifecycle"]["sdk_open_attempts"], 1)

    def test_result_ready_does_not_pass_when_child_exit_hangs(self):
        report = self.run_fake("exit_hang")
        self.assertTrue(report["result_ready"])
        self.assertTrue(report["termination_requested"])
        self.assertEqual(report["status"], "UNVERIFIED")

    def test_spawned_no_callback_is_distinct_from_missing_result(self):
        report = self.run_fake("none")
        self.assertTrue(report["result_ready"])
        self.assertEqual(report["aggregate"]["counts"]["callbacks_received"], 0)
        self.assertEqual(report["status"], "UNVERIFIED")

    def test_spawned_burst_has_no_false_timestamp_rejection(self):
        report = self.run_fake("burst")
        self.assertTrue(report["result_ready"])
        self.assertGreater(report["aggregate"]["counts"]["callbacks_received"], 100)
        self.assertEqual(report["aggregate"]["counts"]["receive_order_rejections"], 0)

    def test_spawned_malformed_frame_is_sanitized_abort(self):
        report = self.run_fake("malformed")
        self.assertTrue(report["result_ready"])
        self.assertEqual(report["aggregate"]["abort_reason"], "INVALID_POSE_COUNT")
        self.assertEqual(report["status"], "ABORTED")

    def test_packet_filter_drops_unknown_keys_rejects_private_strings(self):
        template = LiveRetargetSafetyProbe(ProbeConfig()).aggregate_result()
        packet = {"stage": "heartbeat", "aggregate": dict(template, raw_pose=[1, 2, 3]),
                  "private_diagnostic": "SECRET"}
        cleaned = _clean_packet(packet, template)
        self.assertNotIn("raw_pose", cleaned["aggregate"])
        self.assertNotIn("private_diagnostic", cleaned)
        packet["aggregate"]["abort_reason"] = "SECRET"
        with self.assertRaises(ValueError):
            _clean_packet(packet, template)
        with self.assertRaises(ValueError):
            _clean_packet({"stage": "heartbeat", "elapsed_seconds": float("nan")}, template)
        with self.assertRaises(ValueError):
            _clean_packet({"stage": "result_ready"}, template)
        with self.assertRaises(ValueError):
            _clean_packet({"stage": "result_ready", "aggregate": {"status": "PASS"}}, template)

    def test_invalid_configuration_rejected_without_spawn(self):
        config = ProbeConfig(duration_seconds=1)
        for updates in ({"port": True}, {"process_id": 0}, {"hard_timeout_seconds": 61},
                        {"hard_timeout_seconds": float("nan")}, {"hard_timeout_seconds": 1}):
            values = dict(sdk_root=Path(__file__).parent, port=7690,
                          process_id=os.getpid(), config=config, hard_timeout_seconds=3)
            values.update(updates)
            with self.assertRaises(ValueError):
                supervise_probe(**values)

    def test_interrupted_start_cleans_up_owned_child(self):
        context, child, receiver, sender = (MagicMock() for _ in range(4))
        context.Pipe.return_value = (receiver, sender)
        context.Process.return_value = child
        child.pid, child.exitcode = 123, -1
        child.is_alive.return_value = True
        child.terminate.side_effect = lambda: setattr(child.is_alive, "return_value", False)
        # A spawn interruption must still clean up the exact owned child.
        child.start.side_effect = KeyboardInterrupt
        with patch("research.supervised_retarget_probe.multiprocessing.get_context", return_value=context):
            report = supervise_probe(sdk_root=Path(__file__).parent, port=7690,
                process_id=os.getpid(), config=ProbeConfig(duration_seconds=1),
                hard_timeout_seconds=2)
        child.terminate.assert_called_once()
        self.assertEqual(report["status"], "UNVERIFIED")
        self.assertTrue(report["termination_requested"])
        self.assertTrue(report["within_deadline"])

    def test_partial_ipc_reader_cannot_hold_parent_deadline(self):
        context, child, receiver, sender = (MagicMock() for _ in range(4))
        context.Pipe.return_value = (receiver, sender)
        context.Process.return_value = child
        child.pid, child.exitcode = 123, -1
        child.is_alive.return_value = True
        child.join.side_effect = lambda seconds: time.sleep(min(seconds, 0.01))
        child.terminate.side_effect = lambda: setattr(child.is_alive, "return_value", False)
        blocked = threading.Event()
        def partial_frame(_maximum):
            blocked.wait(10)
            raise EOFError
        receiver.recv_bytes.side_effect = partial_frame
        try:
            with patch("research.supervised_retarget_probe.multiprocessing.get_context", return_value=context):
                report = supervise_probe(sdk_root=Path(__file__).parent, port=7690,
                    process_id=os.getpid(), config=ProbeConfig(duration_seconds=1),
                    hard_timeout_seconds=2)
        finally:
            blocked.set()
        self.assertTrue(report["within_deadline"])
        self.assertTrue(report["termination_requested"])
        self.assertIsNone(report["latest_checkpoint"])

    def test_sdk_diagnostics_suppressed_on_captured_python_and_native_streams(self):
        code = ("from research.supervised_retarget_probe import _silence_child; "
                "import os, sys; _silence_child(); "
                "print('PRIVATE_SYNTHETIC', flush=True); "
                "os.write(1, b'PRIVATE_SYNTHETIC'); os.write(2, b'PRIVATE_SYNTHETIC')")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=5,
                                cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")
        self.assertNotIn("rebocap_ws_sdk", sys.modules)


if __name__ == "__main__":
    unittest.main()
