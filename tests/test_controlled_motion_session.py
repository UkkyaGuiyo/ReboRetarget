"""Synthetic marker timing and one spawned interactive-session acceptance path."""
from functools import partial
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

from research.controlled_motion_session import ControlledMotionSession, clean_session_status
from research.live_retarget_safety_probe import LiveRetargetSafetyProbe, ProbeConfig
from research.supervised_retarget_probe import (supervise_probe, stdin_command_source,
    print_motion_status, MAX_PACKET_BYTES, _clean_packet)
from tests.synthetic_fixtures import synthetic_human_skeleton
from tests.test_supervised_retarget_probe import synthetic_loader
from tests import test_controlled_motion_analysis as analysis_tests
from tests.test_live_retarget_safety_probe import ManualClock, IDENTITY_POSE


class ControlledMotionSessionTests(unittest.TestCase):
    def setUp(self):
        helper = analysis_tests.ControlledMotionAnalysisTests()
        helper.setUp()
        self.frame = helper.frame
        self.session = ControlledMotionSession("right", helper.bind, started=0.)
        self.sequence = 0

    def consume(self, count, now, frame=None):
        frame = frame or self.frame()
        for i in range(count):
            self.sequence += 1
            self.session.consume(self.sequence, now+i*.001, frame.delta_pose,
                                 frame.canonical, frame.anchors)

    def test_one_cue_complete_exact_windows_and_clear_ram(self):
        self.session.command("baseline", 1.)
        self.consume(60, 1.)
        self.assertEqual(self.session.state, "READY_MOVE")
        self.session.command("move", 2.)
        self.session.command("hold", 3.)
        self.consume(20, 3., self.frame(root=(.3,1.,0.)))
        self.session.command("return", 4.)
        self.session.command("neutral", 5.)
        self.consume(20, 5.)
        self.assertEqual(self.session.poll(6.), "COMPLETE")
        self.assertEqual(self.session.cue_result["result"], "PASS")
        self.assertEqual(self.session.counts, dict(baseline=60, held=20, returned=20))
        self.assertEqual(sum(map(len, self.session._windows.values())), 0)
        status = clean_session_status(self.session.status(6.), "right")
        packet = _clean_packet({"stage": "motion_state", "motion": status}, {}, "right")
        self.assertLess(len(json.dumps(packet).encode()), MAX_PACKET_BYTES)

    def test_received_sample_before_marker_is_excluded(self):
        self.session.command("baseline", 2.)
        self.consume(1, 1.)
        self.assertEqual(self.session.counts["baseline"], 0)
        self.consume(1, 2.)
        self.assertEqual(self.session.counts["baseline"], 1)

    def test_marker_timeout_twenty_seconds_not_ninety_callbacks(self):
        self.assertEqual(self.session.poll(19.999), "CONTINUE")
        self.assertEqual(self.session.poll(20.), "COMPLETE")
        self.assertEqual(self.session.reason, "MARKER_TIMEOUT")
        self.assertEqual(self.session.state, "INCOMPLETE")

    def test_cue_cutoff_and_return_can_finish_after_cutoff(self):
        self.session.command("baseline", 19.)
        self.consume(60, 45.)
        self.session.command("move", 46.)
        self.assertEqual(self.session.reason, "CUE_CUTOFF")

    def test_invalid_command_and_stop_clear_windows(self):
        self.session.command("baseline", 1.)
        self.consume(1, 1.)
        self.session.command("hold", 2.)
        self.assertEqual(self.session.state, "ABORTED")
        self.assertEqual(self.session.reason, "INVALID_COMMAND")
        self.assertEqual(sum(map(len, self.session._windows.values())), 0)

    def test_duplicate_sequence_aborts_and_status_rejects_raw_fields(self):
        self.session.command("baseline", 1.)
        self.consume(1, 1.)
        frame = self.frame()
        self.session.consume(self.sequence, 2., frame.delta_pose, frame.canonical, frame.anchors)
        self.assertEqual(self.session.reason, "SEQUENCE_ORDER")
        value = self.session.status(3.)
        value["raw_pose"] = [1, 2]
        with self.assertRaises(ValueError):
            clean_session_status(value, "right")

    def test_original_delta_canonical_stay_coherent_during_concurrent_replace(self):
        clock = ManualClock(1.)
        observed = []
        probe = LiveRetargetSafetyProbe(ProbeConfig(), clock=clock,
            pose_observer=lambda seq, receive, delta, canonical, anchors:
                observed.append((seq, delta.root_translation, canonical.root_translation)))
        probe.on_pose(None, (1.,1.,0.), IDENTITY_POSE, -1, 1.)
        from research.live_retarget_safety_probe import retarget_pose
        def replace_during_fk(*args):
            clock.advance(.01)
            probe.on_pose(None, (2.,1.,0.), IDENTITY_POSE, -1, 2.)
            return retarget_pose(*args)
        with patch("research.live_retarget_safety_probe.retarget_pose", side_effect=replace_during_fk):
            probe.process_latest()
        self.assertEqual(observed, [(1, (1.,1.,0.), (1.,1.,0.))])

    def test_spawned_single_session_completes_without_user_stop(self):
        current, sent = {}, set()
        def status(value):
            current.update(value)
        def commands():
            state = current.get("state")
            command = {"WAIT_BASELINE": "baseline", "READY_MOVE": "move", "WAIT_HOLD": "hold",
                       "READY_RETURN": "return", "WAIT_NEUTRAL": "neutral"}.get(state)
            if command is not None and state not in sent:
                sent.add(state)
                return command
            return None
        report = supervise_probe(sdk_root=Path(__file__).parent, port=7690, process_id=os.getpid(),
            config=ProbeConfig(duration_seconds=8, consumer_hz=120, stale_after_seconds=1,
                               minimum_callbacks=20, pure_pipeline_p99_budget_ms=100),
            hard_timeout_seconds=10, motion_cue="right", command_source=commands,
            status_observer=status, _sdk_loader=partial(synthetic_loader, mode="success"))
        self.assertTrue(report["within_deadline"])
        self.assertTrue(report["result_ready"])
        self.assertFalse(report["termination_requested"])
        self.assertEqual(report["aggregate"]["abort_reason"], "NONE")
        self.assertTrue(report["aggregate"]["lifecycle"]["controlled_completion"])
        self.assertEqual(report["motion"]["state"], "COMPLETE")
        self.assertEqual(report["motion"]["counts"], dict(baseline=60,held=20,returned=20))
        self.assertEqual(report["control_commands_sent"], 5)

    def test_motion_cli_omits_absolute_clocks_without_mutating_api_report(self):
        from research.supervised_retarget_probe import main
        api_report = dict(status="PASS", start_perf_counter=1., deadline_perf_counter=61.,
                          end_perf_counter=30., child_pid=123, elapsed_seconds=29.)
        output = StringIO()
        with patch("research.supervised_retarget_probe.supervise_probe", return_value=api_report), \
             patch("research.supervised_retarget_probe.stdin_command_source", return_value=lambda: None), \
             patch("research.supervised_retarget_probe.signal.signal"), redirect_stdout(output):
            self.assertEqual(main(["--sdk-root", ".", "--port", "7690", "--process-id", "123",
                "--motion-cue", "right", "--duration-seconds", "55", "--hard-timeout-seconds", "60"]), 0)
        public = json.loads(output.getvalue().split("RESULT_JSON=", 1)[1])
        for key in ("start_perf_counter", "deadline_perf_counter", "end_perf_counter", "child_pid"):
            self.assertNotIn(key, public)
            self.assertIn(key, api_report)


def interactive_synthetic():
    """Manual PTY acceptance ONLY: fake SDK never imports vendor or uses a socket."""
    report = supervise_probe(sdk_root=Path(__file__).parent, port=7690, process_id=os.getpid(),
        config=ProbeConfig(duration_seconds=55, consumer_hz=30), hard_timeout_seconds=60,
        motion_cue="right", command_source=stdin_command_source(),
        status_observer=print_motion_status, _sdk_loader=partial(synthetic_loader, mode="success"))
    print("RESULT_JSON="+json.dumps(report, allow_nan=False), flush=True)
    return 0 if report["child_exit_observed"] else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--interactive-synthetic"]:
        os._exit(interactive_synthetic())
    unittest.main()
