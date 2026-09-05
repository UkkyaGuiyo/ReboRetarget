"""Silent synthetic validation of the exact countdown wrapper/supervisor path."""
from functools import partial
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research.countdown_motion_cue import CountdownCue, LocalSpeech, run_countdown


class ManualClock:
    def __init__(self):
        self.value = 0.
    def __call__(self):
        return self.value


class FakeSpeech:
    def __init__(self, clock, delay=0., result=0):
        self.clock, self.done_at, self.result = clock, clock()+delay, result
        self.cancelled = False
    def poll(self):
        return -1 if self.cancelled else self.result if self.clock() >= self.done_at else None
    def cancel(self):
        self.cancelled = True
    def close(self, timeout):
        self.cancel()
        return True


class SilentSpeech(LocalSpeech):
    """Real owned subprocess, same poll/cancel/close; never calls an audio API."""
    def __init__(self, delay, result):
        self.process = subprocess.Popen(
            [sys.executable, "-c", "import sys,time;time.sleep(float(sys.argv[1]));sys.exit(int(sys.argv[2]))",
             str(delay), str(result)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)


class CountdownFakeSdk:
    def __init__(self, mode, **options):
        assert options == dict(coordinate_type="synthetic_unity", use_global_rotation=True)
        self.mode, self.stop, self.thread = mode, threading.Event(), None
    def set_pose_msg_callback(self, callback):
        self.callback = callback
    def set_exception_close_callback(self, callback):
        self.close_callback = callback
    def open(self, port):
        assert port == 7690
        if self.mode == "open_hang":
            time.sleep(3600)
        if self.mode != "none":
            def produce():
                sequence = 0
                while not self.stop.is_set():
                    for _ in range(4 if self.mode == "burst" else 1):
                        self.callback(self, (0.,1.,0.), ((1.,0.,0.,0.),)*24, -1, sequence/60.)
                        sequence += 1
                    self.stop.wait(.4 if self.mode == "late" else 1/60)
            self.thread = threading.Thread(target=produce, daemon=True)
            self.thread.start()
        return 0
    def close(self):
        self.stop.set()
        if self.thread is not None:
            self.thread.join(.3)
        if self.mode == "close_hang":
            time.sleep(3600)


def countdown_sdk_loader(_path, *, mode):
    return SimpleNamespace(CoordinateType=SimpleNamespace(UnityCoordinate="synthetic_unity"),
                           RebocapWsSdk=partial(CountdownFakeSdk, mode))


class CountdownUnitTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.jobs = ManualClock(), []
        def factory(cue, returning):
            job = FakeSpeech(self.clock)
            self.jobs.append((returning, job))
            return job
        self.controller = CountdownCue("right", clock=self.clock, speech_factory=factory)

    def state(self, state):
        self.controller.on_status(dict(cue="right", state=state))

    def test_commands_wait_for_child_ack_then_four_second_settle(self):
        self.assertIsNone(self.controller())
        self.state("WAIT_BASELINE")
        self.assertEqual(self.controller(), "baseline")
        self.state("READY_MOVE")
        self.assertEqual(self.controller(), "move")
        self.assertEqual(self.jobs, [])
        self.assertIsNone(self.controller())
        self.state("WAIT_HOLD")
        self.assertIsNone(self.controller())
        self.assertEqual(len(self.jobs), 1)
        self.clock.value = 3.99
        self.assertIsNone(self.controller())
        self.clock.value = 4.
        self.assertEqual(self.controller(), "hold")
        self.state("READY_RETURN")
        self.assertEqual(self.controller(), "return")
        self.assertEqual(len(self.jobs), 1)
        self.state("WAIT_NEUTRAL")
        self.assertIsNone(self.controller())
        self.clock.value = 8.
        self.assertEqual(self.controller(), "neutral")
        self.state("COMPLETE")
        self.assertIsNone(self.controller())
        self.assertEqual(self.controller.commands_sent, 5)
        self.assertEqual(self.controller.evidence()["user_confirmation"], "PENDING")
        self.assertEqual(self.controller.evidence()["speech_audibility"], "UNVERIFIED")

    def test_late_successful_poll_is_timeout_not_hold(self):
        self.controller.phase = "WAIT_MOVE_ACCEPTED"
        self.state("WAIT_HOLD")
        self.controller.speech_factory = lambda *_: FakeSpeech(self.clock, 12.1)
        self.controller()
        self.clock.value = 12.2
        self.assertEqual(self.controller(), "stop")
        self.assertEqual(self.controller.error, "SPEECH_TIMEOUT")
        self.assertIsNone(self.controller())

    def test_bad_clock_cutoff_stop_and_terminal_cancel(self):
        self.clock.value = float("nan")
        self.assertEqual(self.controller(), "stop")
        self.assertEqual(self.controller.error, "CLOCK_ORDER")
        clock = ManualClock()
        controller = CountdownCue("right", clock=clock)
        controller.phase = "WAIT_READY_MOVE"
        controller.on_status(dict(cue="right", state="READY_MOVE"))
        clock.value = 45
        self.assertEqual(controller(), "stop")
        self.assertEqual(controller.error, "CUE_CUTOFF")

    def test_readiness_fail_closed_without_spawn(self):
        with patch("research.countdown_motion_cue.supervise_probe") as probe:
            for value in (False, None, 1):
                with self.assertRaises(ValueError):
                    run_countdown(sdk_root=Path("."), port=7690, process_id=os.getpid(),
                                  cue="right", user_ready=value)
            probe.assert_not_called()

    def test_only_clean_zero_input_countdown_timeout_is_unverified(self):
        from copy import deepcopy
        clean = dict(status="ABORTED", child_exit_observed=True, child_exit_code=0,
            result_ready=True, supervisor_reason="CHILD_EXIT", within_deadline=True,
            termination_requested=False, termination_error=False, invalid_packet_count=0,
            aggregate=dict(abort_reason="USER_STOP", counts=dict(callbacks_received=0),
                lifecycle=dict(sdk_open_successes=1, sdk_close_successes=1)))
        for variation in ("clean", "user_stop", "forced", "protocol", "sdk_fault", "some_input"):
            report = deepcopy(clean)
            if variation == "forced": report["termination_requested"] = True
            if variation == "protocol": report["invalid_packet_count"] = 1
            if variation == "sdk_fault": report["aggregate"]["abort_reason"] = "SDK_OPEN_FAILED"
            if variation == "some_input": report["aggregate"]["counts"]["callbacks_received"] = 1
            def fake_probe(**kwargs):
                kwargs["command_source"]._fail("USER_STOP" if variation == "user_stop" else "COUNTDOWN_DEADLINE")
                return report
            with self.subTest(variation=variation), patch(
                    "research.countdown_motion_cue.supervise_probe", side_effect=fake_probe):
                result = run_countdown(sdk_root=Path("."), port=7690, process_id=os.getpid(),
                    cue="right", user_ready=True, _speech_factory=FakeSpeech)
                self.assertEqual(result["status"], "UNVERIFIED" if variation == "clean" else "ABORTED")

    def test_speech_uses_hidden_local_standard_process_without_executing(self):
        with patch("research.countdown_motion_cue.subprocess.Popen") as launch, \
             patch("research.countdown_motion_cue.sys.platform", "win32"):
            LocalSpeech("right", False)
        arguments, options = launch.call_args
        self.assertEqual(arguments[0][0], "powershell.exe")
        self.assertIn("System.Speech", arguments[0][-1])
        self.assertIn("ja-JP", arguments[0][-1])
        self.assertEqual(options["stdout"], subprocess.DEVNULL)
        self.assertEqual(options["stderr"], subprocess.DEVNULL)
        self.assertTrue(options["creationflags"] & subprocess.CREATE_NO_WINDOW)


class CountdownWrapperTests(unittest.TestCase):
    """Default production bounds, real SDK child, real silent speech processes.

    Lifecycle hangs deliberately take almost a minute; do not parallelize this
    class with benchmarks. No observation or speech deadline is relaxed.
    """
    def run_case(self, *, mode="normal", delay=.01, speech_result=0,
                 launch_fail=False, user_stop=False):
        jobs, states = [], []
        children_before = {child.pid for child in multiprocessing.active_children()}
        def factory(cue, returning):
            self.assertEqual(cue, "right")
            self.assertIn(states[-1], ("WAIT_HOLD", "WAIT_NEUTRAL"))
            self.assertTrue(all(job.poll() is not None for job in jobs))
            if launch_fail:
                raise OSError("synthetic launch failure")
            job = SilentSpeech(delay, speech_result)
            jobs.append(job)
            return job
        def stop_source():
            return "stop" if user_stop and jobs else None
        started = time.perf_counter()
        try:
            report = run_countdown(sdk_root=Path(__file__).parent, port=7690,
                process_id=os.getpid(), cue="right", user_ready=True,
                stop_source=stop_source, status_observer=lambda value: states.append(value["state"]),
                _sdk_loader=partial(countdown_sdk_loader, mode=mode), _speech_factory=factory)
            self.assertLess(time.perf_counter()-started, 60)
            self.assertLessEqual(report["total_elapsed_seconds_including_audio_cleanup"], 60)
            self.assertTrue(report["countdown"]["audio_exit_observed"])
            self.assertTrue(report["child_exit_observed"])
            self.assertTrue(all(job.poll() is not None for job in jobs))
            self.assertEqual({child.pid for child in multiprocessing.active_children()}, children_before)
            self.assertNotEqual(report["status"], "PASS")
            self.assertEqual(report["countdown"]["user_confirmation"], "PENDING")
            return report
        finally:
            for job in jobs:
                job.close(.4)

    def test_exact_wrapper_normal_60_20_20(self):
        report = self.run_case()
        self.assertEqual(report["motion"]["state"], "COMPLETE")
        self.assertEqual(report["motion"]["counts"], dict(baseline=60,held=20,returned=20))
        self.assertEqual(report["aggregate"]["abort_reason"], "NONE")
        self.assertFalse(report["termination_requested"])
        self.assertEqual(report["countdown"]["speech_completed"], 2)

    def test_exact_wrapper_slow_speech_within_budget(self):
        report = self.run_case(delay=1.)
        self.assertEqual(report["motion"]["state"], "COMPLETE")
        self.assertFalse(report["termination_requested"])

    def test_exact_wrapper_speech_exceeds_budget(self):
        report = self.run_case(delay=12.5)
        self.assertEqual(report["status"], "ABORTED")
        self.assertEqual(report["countdown"]["error"], "SPEECH_TIMEOUT")

    def test_exact_wrapper_missing_voice(self):
        report = self.run_case(speech_result=2)
        self.assertEqual(report["countdown"]["error"], "SPEECH_FAILED")

    def test_exact_wrapper_speech_launch_failure(self):
        report = self.run_case(launch_fail=True)
        self.assertEqual(report["countdown"]["error"], "SPEECH_START_FAILED")

    def test_exact_wrapper_never_exiting_speech_is_owned_cleanup(self):
        report = self.run_case(delay=3600)
        self.assertEqual(report["countdown"]["error"], "SPEECH_TIMEOUT")

    def test_exact_wrapper_sdk_open_hang(self):
        report = self.run_case(mode="open_hang")
        self.assertTrue(report["termination_requested"])
        self.assertEqual(report["latest_checkpoint"]["stage"], "open_before")
        self.assertEqual(report["countdown"]["speech_started"], 0)

    def test_exact_wrapper_sdk_close_hang(self):
        report = self.run_case(mode="close_hang")
        self.assertTrue(report["termination_requested"])
        self.assertEqual(report["latest_checkpoint"]["stage"], "close_before")

    def test_exact_wrapper_user_stop_cancels_speech(self):
        report = self.run_case(delay=3600, user_stop=True)
        self.assertEqual(report["status"], "ABORTED")
        self.assertEqual(report["countdown"]["error"], "USER_STOP")

    def test_exact_wrapper_no_callbacks_cannot_complete(self):
        report = self.run_case(mode="none")
        self.assertEqual(report["status"], "UNVERIFIED")
        self.assertNotEqual(report["motion"]["state"], "COMPLETE")
        self.assertEqual(report["aggregate"]["counts"]["callbacks_received"], 0)

    def test_exact_wrapper_late_input_stale_aborts_without_speech(self):
        report = self.run_case(mode="late")
        self.assertEqual(report["aggregate"]["abort_reason"], "STALE_LATEST_POSE")
        self.assertEqual(report["countdown"]["speech_started"], 0)

    def test_exact_wrapper_burst_no_backlog_or_timestamp_replay(self):
        report = self.run_case(mode="burst")
        self.assertEqual(report["motion"]["state"], "COMPLETE")
        self.assertEqual(report["aggregate"]["counts"]["receive_order_rejections"], 0)
        self.assertGreater(report["aggregate"]["counts"]["sequence_gap_drops"], 0)


if __name__ == "__main__":
    unittest.main()
