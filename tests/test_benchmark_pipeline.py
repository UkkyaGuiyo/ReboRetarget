"""Synthetic-only benchmark contract tests, not performance acceptance tests."""
import ast
import gc
import json
import math
from pathlib import Path
import sys
import unittest
import weakref
from unittest.mock import patch

from research import benchmark_pipeline as benchmark_module
from research.benchmark_pipeline import _Run, _load_implementation, benchmark, distribution


class PipelineBenchmarkTests(unittest.TestCase):
    def test_exact_nearest_rank_percentiles_and_empty_count(self):
        summary = distribution(list(range(1, 101)))
        self.assertEqual(summary, dict(count=100, mean_ms=50.5, p50_ms=50,
                                      p95_ms=95, p99_ms=99, max_ms=100))
        self.assertEqual(distribution([])["count"], 0)
        self.assertIsNone(distribution([])["p99_ms"])

    def test_configuration_rejected_before_implementation_load(self):
        for options in ({"samples": True}, {"samples": 0}, {"samples": 2001},
                        {"repeats": 0}, {"warmup": -1}, {"variants": ("A", "A")},
                        {"variants": ("G",)}, {"diagnostic": "unknown"},
                        {"gc_mode": "unknown"}, {"implementation_label": "private path"}):
            with self.subTest(options=options), patch.object(benchmark_module, "_load_implementation") as load:
                with self.assertRaises(ValueError):
                    benchmark(**options)
                load.assert_not_called()

    def test_primary_all_modes_same_value_path_and_aggregate_only(self):
        result = benchmark(variants=tuple("ABCDEF"), samples=100, repeats=1, warmup=1)
        self.assertEqual(result["timing"], "primary_boundary_timing")
        self.assertEqual(result["fixture"], "noncommuting_bind_and_sdk_delta_v1")
        for variant in "ABCDEF":
            row = result["variants"][variant]
            self.assertEqual(row["combined_wall"]["count"], 100)
            self.assertEqual(row["combined_cpu"]["count"], 100)
            self.assertEqual(row["combined_exact_pure_wall"]["count"], 100)
            self.assertEqual(row["runs"][0]["callback_wall"]["count"], 100)
            self.assertEqual(row["runs"][0]["consumer_wall"]["count"], 100)
            evidence = row["runs"][0]["evidence"]
            self.assertEqual(evidence["publish_accepted"], 100)
            self.assertEqual(evidence["processed_unique_sequences"], 100)
            self.assertEqual(evidence["decoded_messages"], 1600)
            self.assertEqual(evidence["completed_analyses"], int(variant == "F"))
            self.assertNotIn("stages", row["runs"][0])
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn(str(Path(__file__).resolve().parents[1]), encoded)
        self.assertNotIn("root_translation", encoded)
        self.assertNotIn("global_rotations", encoded)
        self.assertNotIn("rebocap_ws_sdk", sys.modules)
        self.assertIn("G_supervisor_ipc", result["pending"])
        self.assertIn("H_countdown_wrapper", result["pending"])
        self.assertEqual(result["variants"]["F"]["runs"][0]["analysis_completion_wall"]["count"], 1)

    def test_disabled_observer_cannot_pass_window_verification(self):
        run = _Run(_load_implementation(), "D")
        run.probe._pose_observer = None
        run.prepare_frame()
        run.step()
        with self.assertRaises(ValueError):
            run.verify(1)

    def test_fixture_contains_noncommuting_rotations_and_nonidentity_bind(self):
        implementation = _load_implementation()
        run = _Run(implementation, "A")
        self.assertTrue(all(math.isfinite(v) for q in run.rotations for v in q))
        self.assertTrue(any(abs(v) > .01 for v in run.rotations[0][1:]))
        first = run.probe._source.joints[0].rest_local_rotation
        self.assertNotEqual(first, implementation.core.Quaternion.identity())
        delta = implementation.core.Quaternion(*run.rotations[0])
        self.assertNotEqual(implementation.core.quaternion_multiply(first, delta),
                            implementation.core.quaternion_multiply(delta, first))

    def test_stage_diagnostic_is_separate_and_restores_call_sites(self):
        implementation = _load_implementation()
        original = implementation.probe.retarget_pose
        result = benchmark(variants=("F",), samples=100, repeats=1, warmup=0, diagnostic="stages")
        self.assertIs(implementation.probe.retarget_pose, original)
        self.assertEqual(result["timing"], "diagnostic_not_acceptance_timing")
        row = result["variants"]["F"]
        self.assertIsNone(row["wall_p99_strictly_below_10ms"])
        stages = row["runs"][0]["stages"]
        for stage in benchmark_module.STAGES:
            self.assertGreater(stages[stage]["wall"]["count"], 0, stage)
        self.assertEqual(stages["osc_decode"]["wall"]["count"], 1600)
        self.assertEqual(stages["cue_analysis"]["wall"]["count"], 1)

    def test_opt_in_cpu_profile_allocations_and_gc_restore(self):
        original_gc = gc.isenabled()
        for diagnostic in ("cprofile", "allocations"):
            result = benchmark(samples=2, repeats=1, warmup=0, diagnostic=diagnostic, gc_mode="off")
            self.assertEqual(gc.isenabled(), original_gc)
            row = result["variants"]["A"]["runs"][0]
            if diagnostic == "cprofile":
                self.assertGreater(len(row["profile"]), 0)
                self.assertTrue(all(Path(item["file"]).name == item["file"] for item in row["profile"]))
            else:
                self.assertGreater(row["allocations"]["peak_bytes"], 0)
            self.assertIsNone(result["variants"]["A"]["wall_p99_strictly_below_10ms"])

    def test_missing_observer_snapshot_is_explicitly_unavailable(self):
        implementation = _load_implementation()
        old_session, implementation.session = implementation.session, None
        try:
            with patch.object(benchmark_module, "_load_implementation", return_value=implementation):
                result = benchmark(variants=("B", "F"), samples=1, repeats=1, warmup=0)
        finally:
            implementation.session = old_session
        self.assertEqual(result["variants"]["B"]["status"], "UNAVAILABLE_IN_SNAPSHOT")

    def test_measurement_helpers_do_not_create_reference_cycles(self):
        original_gc = gc.isenabled()
        gc.disable()
        try:
            for variant in ("A", "C"):
                run = _Run(_load_implementation(), variant)
                reference = weakref.ref(run)
                run.prepare_frame()
                run.step()
                del run
                self.assertIsNone(reference())
        finally:
            if original_gc:
                gc.enable()

    def test_source_imports_no_sdk_audio_or_process_transport(self):
        tree = ast.parse(Path(benchmark_module.__file__).read_text(encoding="utf-8"))
        modules = {node.module.split(".")[0] for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module}
        modules |= {alias.name.split(".")[0] for node in ast.walk(tree)
                    if isinstance(node, ast.Import) for alias in node.names}
        self.assertTrue({"subprocess", "socket", "multiprocessing", "rebocap_ws_sdk"}.isdisjoint(modules))

    def test_production_value_bytes_match_full_research_reference(self):
        result = benchmark(path="production-value", samples=3, repeats=1, warmup=1)
        row = result["variants"]["A"]
        self.assertEqual(row["combined_exact_pure_wall"]["count"], 0)
        self.assertIsNone(row["pure_p99_strictly_below_10ms"])
        self.assertTrue(row["runs"][0]["evidence"]["research_reference_bytes_equal"])
        self.assertEqual(row["runs"][0]["evidence"]["encoded_messages"], 48)
        self.assertNotIn("decoded_messages", row["runs"][0]["evidence"])
        with self.assertRaises(ValueError):
            benchmark(path="production-value", variants=("F",))

    def test_gc_pause_diagnostic_is_opt_in_bounded_and_removed(self):
        callbacks = list(gc.callbacks)
        original = _Run.step
        def collected_step(run):
            gc.collect()
            return original(run)
        with patch.object(_Run, "step", new=collected_step):
            result = benchmark(samples=2, repeats=1, warmup=0, diagnostic="gc")
        self.assertEqual(gc.callbacks, callbacks)
        pause = result["variants"]["A"]["runs"][0]["gc_pauses"]
        self.assertGreaterEqual(pause["observed_events"], 2)
        self.assertGreaterEqual(pause["total_ms"], 0)
        self.assertLessEqual(pause["count"], 10000)
        self.assertEqual(pause["observed_events"], pause["count"] + pause["overflow_events"])
        self.assertEqual(result["timing"], "diagnostic_not_acceptance_timing")

    def test_gc_diagnostic_restores_callbacks_and_policy_on_error(self):
        callbacks, enabled = list(gc.callbacks), gc.isenabled()
        with patch.object(_Run, "step", side_effect=ValueError("synthetic failure")):
            with self.assertRaises(ValueError):
                benchmark(samples=1, repeats=1, warmup=0, diagnostic="gc", gc_mode="off")
        self.assertEqual(gc.callbacks, callbacks)
        self.assertEqual(gc.isenabled(), enabled)


if __name__ == "__main__":
    unittest.main()
