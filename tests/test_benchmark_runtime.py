"""Synthetic only; run serially with performance measurements paused."""
import json
import multiprocessing
from pathlib import Path
import unittest
from unittest.mock import patch

from research.benchmark_runtime import _distribution, _load, benchmark


class RuntimeBenchmarkTests(unittest.TestCase):
    def test_exact_nearest_rank_not_histogram_edges(self):
        self.assertEqual(_distribution([])["count"], 0)
        result = _distribution([.11, .22, .33, .44])
        self.assertEqual(result["p50_ms"], .22)
        self.assertEqual(result["p99_ms"], .44)
        self.assertEqual(result["count"], 4)

    def test_invalid_configuration_does_not_load_or_spawn(self):
        with patch("research.benchmark_runtime._load") as load:
            for kwargs in (dict(duration=0), dict(duration=float("nan")),
                           dict(repeats=4), dict(repeats=True), dict(modes=("live",)),
                           dict(modes=("G0", "G0")), dict(consumer_rates=(120,)),
                           dict(implementation_label="private-path")):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    benchmark(**kwargs)
            load.assert_not_called()

    def test_already_imported_implementation_cannot_be_swapped(self):
        from research import live_retarget_safety_probe
        with self.assertRaises(ValueError):
            _load(Path(live_retarget_safety_probe.__file__).parent / "missing")

    def check_report(self, report):
        encoded = json.dumps(report, allow_nan=False)
        for forbidden in (str(Path(__file__).resolve().parents[1]), "child_pid",
                          "source_timestamp", "start_perf_counter", "sdk_root"):
            # The privacy statement names the excluded category, never its value.
            if forbidden != "source_timestamp":
                self.assertNotIn(forbidden, encoded)
        for row in report["rows"]:
            self.assertTrue(row["clean_child_exit"])
            self.assertTrue(row["within_deadline"])
            self.assertFalse(row["forced_termination"])
            self.assertEqual(row["invalid_packets"], 0)
            self.assertGreater(row["counts"]["processed_unique_sequences"], 0)
            # Windows process CPU accounting can quantize a short fast run to zero.
            self.assertGreaterEqual(row["child_cpu_seconds"], 0)
            self.assertGreater(row["stage_wall_exact_nearest_rank"]["callback"]["count"], 0)
            self.assertGreater(row["stage_wall_exact_nearest_rank"]["wait_actual"]["count"], 0)

    def test_three_groups_use_actual_same_supervisor_and_clean_owned_child(self):
        children = {child.pid for child in multiprocessing.active_children()}
        report = benchmark(duration=1., consumer_rates=(30.,))
        self.check_report(report)
        g0, g1, g2 = report["rows"]
        self.assertEqual(g0["progress_calls"], 0)
        self.assertGreater(g1["progress_calls"], 0)
        self.assertGreater(g2["checkpoint_count"], g1["checkpoint_count"])
        self.assertGreater(g1["stage_wall_exact_nearest_rank"]["aggregate"]["count"],
                           g0["stage_wall_exact_nearest_rank"]["aggregate"]["count"])
        self.assertEqual({child.pid for child in multiprocessing.active_children()}, children)

    def test_requested_sixty_hz_same_value_path(self):
        report = benchmark(modes=("G2",), duration=1., consumer_rates=(60.,))
        self.check_report(report)
        self.assertEqual(report["rows"][0]["configured_consumer_hz"], 60.)

    def test_h_exact_countdown_wrapper_silent_job(self):
        report = benchmark(modes=("H",), consumer_rates=(30.,))
        self.check_report(report)
        row = report["rows"][0]
        self.assertEqual(row["motion_state"], "COMPLETE")
        self.assertEqual(row["motion_counts"], dict(baseline=60, held=20, returned=20))
        self.assertEqual(row["countdown_error"], "NONE")
        self.assertLess(row["wrapper_total_including_cleanup_seconds"], 60.)
        self.assertNotEqual(row["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
