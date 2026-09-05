"""Offline comparison of the real probe value path; no SDK, audio or transport.

Primary runs time only the outer frame boundary. Optional stage/profile/allocation
diagnostics deliberately run separately and must not be compared to Live timing.
Use a fresh CLI process per --implementation-root to compare source snapshots.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import cProfile
import gc
import importlib
import inspect
import json
import math
from pathlib import Path
import pstats
import sys
import time
import tracemalloc
import weakref
from types import SimpleNamespace
from unittest.mock import patch

VARIANTS = {
    "A": "probe_without_observer",
    "B": "session_instantiated_observer_disabled",
    "C": "observer_no_collection",
    "D": "baseline_collection",
    "E": "held_window_collection",
    "F": "complete_60_20_20_analysis",
}
STAGES = (
    "validation", "delta_construction", "adapter", "latest_publish", "latest_snapshot",
    "target_fk", "anchors", "euler", "osc_representation", "osc_messages",
    "osc_encode", "osc_decode", "observer", "cue_state", "cue_analysis", "metrics",
)


def distribution(values: list[float]) -> dict:
    """Exact nearest-rank percentiles in milliseconds, not histogram lower edges."""
    ordered = sorted(values)
    def percentile(fraction):
        return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)] if ordered else None
    return {"count": len(ordered), "mean_ms": sum(ordered) / len(ordered) if ordered else None,
            "p50_ms": percentile(.50), "p95_ms": percentile(.95),
            "p99_ms": percentile(.99), "max_ms": ordered[-1] if ordered else None}


def _load_implementation(root: Path | None = None) -> SimpleNamespace:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    if not (root / "research" / "live_retarget_safety_probe.py").is_file():
        raise ValueError("implementation snapshot is unavailable")
    existing = sys.modules.get("research.live_retarget_safety_probe")
    if existing is not None and root not in Path(existing.__file__).resolve().parents:
        raise ValueError("use a fresh process for another implementation snapshot")
    sys.path.insert(0, str(root))
    probe = importlib.import_module("research.live_retarget_safety_probe")
    core = importlib.import_module("reboretarget")
    fixtures = importlib.import_module("tests.synthetic_fixtures")
    osc = importlib.import_module("reboretarget.vrchat_osc")
    session = None
    if "pose_observer" in inspect.signature(probe.LiveRetargetSafetyProbe).parameters:
        session = importlib.import_module("research.controlled_motion_session")
    return SimpleNamespace(root=root, probe=probe, core=core, fixtures=fixtures,
                           osc=osc, session=session)


class _Run:
    """One bounded synthetic episode sequence, using unchanged runtime validation."""
    def __init__(self, implementation, variant, path="research"):
        self.i, self.variant, self.sequence, self.session = implementation, variant, 0, None
        self.path, self.production_count, self.production_packets = path, 0, ()
        core, module = implementation.core, implementation.probe
        original_fixture = implementation.fixtures.synthetic_human_skeleton
        self.bind_overrides = {
            "Pelvis": core.quaternion_from_axis_angle((1, 0, 0), 23),
            "Spine3": core.quaternion_from_axis_angle((0, 1, 0), -17),
            "L_Shoulder": core.quaternion_from_axis_angle((0, 0, 1), 31),
        }
        def fixture(**kwargs):
            return original_fixture(**dict(kwargs, rest_local_rotation_overrides=self.bind_overrides))
        arguments = {}
        if variant not in ("A", "B"):
            run_reference = weakref.ref(self)
            def observer(*args):
                run_reference().observe(*args)
            arguments["pose_observer"] = observer
        # Inject at construction, so prepared source/target caches use this bind too.
        with patch.object(module, "synthetic_human_skeleton", new=fixture):
            self.probe = module.LiveRetargetSafetyProbe(module.ProbeConfig(), **arguments)
        self.pure_values = []
        self.callback_wall, self.callback_cpu = [], []
        self.consumer_wall, self.consumer_cpu = [], []
        histogram = self.probe.histograms["pure_pipeline"]
        original_add, histogram_reference, pure_values = type(histogram).add, weakref.ref(histogram), self.pure_values
        def retain_finished_pure_sample(value):
            # The real probe captured both endpoints before calling histogram.add.
            # Preserve its histogram and retain the exact synthetic duration only.
            original_add(histogram_reference(), value)
            pure_values.append(value)
        histogram.add = retain_finished_pure_sample
        self.rotations = tuple(tuple(getattr(q, field) for field in ("w", "x", "y", "z"))
            for q in (core.quaternion_multiply(
                core.quaternion_from_axis_angle((1, 2, 0), 13 + index % 7),
                core.quaternion_from_axis_angle((0, 1, 3), -9 - index % 5)) for index in range(24)))
        self.baseline_root, self.held_root = (0., 1., 0.), (.3, 1., 0.)
        delta = core.ReboCapDeltaPose.from_rebocap24(self.baseline_root, self.rotations)
        canonical = core.adapt_rebocap_delta_pose(delta, self.probe._source)
        target = core.retarget_pose(canonical, self.probe._source, self.probe._target)
        anchors = core.build_tracker_transforms(target, self.probe._anchors)
        self.prepared_baseline = (delta, canonical, anchors)
        self.production_slot = core.LatestPoseSlot(self.probe.config.stale_after_seconds)
        self.completed_analyses = 0
        if variant in ("B", "C"):
            self.new_session()

    def new_session(self):
        self.session = self.i.session.ControlledMotionSession(
            "right", self.probe._source, started=time.perf_counter())

    def prepare_frame(self):
        """Episode setup outside measurements; actual markers stay inside step()."""
        variant = self.variant
        if variant == "D" and self.sequence % 60 == 0:
            self.new_session()
        elif variant == "E" and self.sequence % 20 == 0:
            self.new_session()
            self.session.command("baseline", time.perf_counter())
            # Prime the known baseline outside the held-only comparison window.
            for sequence in range(1, 61):
                self.session.consume(sequence, time.perf_counter(), *self.prepared_baseline)
        elif variant == "F" and self.sequence % 100 == 0:
            self.new_session()

    def step(self):
        variant, offset = self.variant, self.sequence % 100
        root = self.baseline_root
        if variant == "D" and self.sequence % 60 == 0:
            self.session.command("baseline", time.perf_counter())
        elif variant == "E":
            root = self.held_root
            if self.sequence % 20 == 0:
                self.session.command("move", time.perf_counter())
                self.session.command("hold", time.perf_counter())
        elif variant == "F":
            if offset == 0:
                self.session.command("baseline", time.perf_counter())
            elif offset == 60:
                self.session.command("move", time.perf_counter())
                self.session.command("hold", time.perf_counter())
            elif offset == 80:
                self.session.command("return", time.perf_counter())
                self.session.command("neutral", time.perf_counter())
            if 60 <= offset < 80:
                root = self.held_root
        self.sequence += 1
        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
        if self.path == "research":
            self.probe.on_pose(None, root, self.rotations, -1, self.sequence / 60.0)
        else:
            receive = time.perf_counter()
            checked_root, checked_rotations, source_time = self.probe._raw_values(
                root, self.rotations, self.sequence / 60.0)
            delta = self.i.core.ReboCapDeltaPose.from_rebocap24(checked_root, checked_rotations)
            prepared = getattr(self.probe, "_prepared_adapter", None)
            canonical = (prepared.adapt(delta) if prepared is not None
                         else self.i.core.adapt_rebocap_delta_pose(delta, self.probe._source))
            if self.production_slot.publish(canonical, receive_monotonic=receive,
                    source_timestamp=source_time) is not self.i.core.PublishResult.ACCEPTED:
                raise ValueError("synthetic production publish failed")
        callback_cpu = (time.process_time_ns() - cpu) / 1e6
        callback_wall = (time.perf_counter_ns() - wall) / 1e6
        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
        if self.path == "research":
            self.probe.process_latest()
        else:
            snapshot = self.production_slot.snapshot_at(time.perf_counter())
            if snapshot.state is not self.i.core.LatestPoseState.VALID or snapshot.sample is None:
                raise ValueError("synthetic production latest is not valid")
            target = self.i.core.retarget_pose(snapshot.sample.value, self.probe._source, self.probe._target)
            anchors = self.i.core.build_tracker_transforms(target, self.probe._anchors)
            poses = self.i.core.build_osc_tracker_poses(anchors)
            messages = self.i.core.build_tracker_messages(poses)
            self.production_packets = tuple(self.i.core.encode_osc_float3_message(message) for message in messages)
            self.production_count += 1
        consumer_cpu = (time.process_time_ns() - cpu) / 1e6
        consumer_wall = (time.perf_counter_ns() - wall) / 1e6
        self.callback_cpu.append(callback_cpu)
        self.callback_wall.append(callback_wall)
        self.consumer_cpu.append(consumer_cpu)
        self.consumer_wall.append(consumer_wall)
        if variant == "F" and self.session.state == "COMPLETE":
            if self.session.cue_result["result"] != "PASS":
                raise ValueError("synthetic controlled result changed")
            self.completed_analyses += 1

    def observe(self, sequence, receive, delta, canonical, anchors):
        # E's synthetic baseline uses local 1..60 before the measured held frames.
        if self.variant == "E":
            sequence = 61 + (self.sequence - 1) % 20
        self.session.consume(sequence, receive, delta, canonical, anchors)

    def verify(self, count):
        if self.path == "production-value":
            if self.production_count != count:
                raise ValueError("synthetic production frame count changed")
            if count:
                # Compare with the unchanged full research validation/decode path
                # outside every timed measurement. Never persist these packets.
                reference, packets = _Run(self.i, "A"), []
                encode = self.i.probe.encode_osc_float3_message
                def capture(message):
                    packet = encode(message)
                    packets.append(packet)
                    return packet
                with patch.object(self.i.probe, "encode_osc_float3_message", new=capture):
                    reference.step()
                reference.verify(1)
                if tuple(packets) != self.production_packets or len(packets) != 16:
                    raise ValueError("production and research bytes differ")
            return dict(publish_accepted=count, processed_unique_sequences=count,
                        pipeline_successes=count, encoded_messages=count * 16,
                        research_reference_bytes_equal=True, completed_analyses=0)
        report = self.probe.aggregate_result()
        expected = {"publish_accepted": count, "processed_unique_sequences": count,
                    "pipeline_successes": count, "decoded_messages": count * 16}
        if report["abort_reason"] != "NONE" or any(report["counts"][k] != v for k, v in expected.items()):
            raise ValueError("synthetic value path did not complete")
        if self.completed_analyses != (count // 100 if self.variant == "F" else 0):
            raise ValueError("synthetic analysis completion count changed")
        if count and self.session is not None:
            counts = {"baseline": 0, "held": 0, "returned": 0}
            if self.variant == "D":
                counts["baseline"] = (count - 1) % 60 + 1
            elif self.variant == "E":
                counts.update(baseline=60, held=(count - 1) % 20 + 1)
            elif self.variant == "F":
                offset = (count - 1) % 100 + 1
                counts.update(baseline=min(offset, 60), held=max(0, min(offset - 60, 20)),
                              returned=max(0, offset - 80))
            if self.session.counts != counts:
                raise ValueError("synthetic observer window counts changed")
        return dict(expected, completed_analyses=self.completed_analyses)


def _stage_wrappers(implementation, recorder, stack, run):
    """Temporary diagnostic call-site wrappers; never enabled for primary timing."""
    probe, core, osc = implementation.probe, implementation.core, implementation.osc
    def wrap(owner, name, stage):
        original = getattr(owner, name)
        def measured(*args, **kwargs):
            wall, cpu = time.perf_counter_ns(), time.process_time_ns()
            try:
                return original(*args, **kwargs)
            finally:
                recorder[stage][0].append((time.perf_counter_ns() - wall) / 1e6)
                recorder[stage][1].append((time.process_time_ns() - cpu) / 1e6)
        stack.enter_context(patch.object(owner, name, new=measured))
    for owner, name, stage in (
        (probe.LiveRetargetSafetyProbe, "_raw_values", "validation"),
        (core.ReboCapDeltaPose, "from_rebocap24", "delta_construction"),
        (core.LatestPoseSlot, "publish", "latest_publish"),
        (core.LatestPoseSlot, "snapshot_at", "latest_snapshot"),
        (probe, "retarget_pose", "target_fk"),
        (probe, "build_tracker_transforms", "anchors"),
        (osc, "quaternion_to_vrchat_euler_degrees", "euler"),
        (probe, "build_osc_tracker_poses", "osc_representation"),
        (probe, "build_tracker_messages", "osc_messages"),
        (probe, "encode_osc_float3_message", "osc_encode"),
        (probe, "decode_osc_float3_message", "osc_decode"),
        (probe.LiveRetargetSafetyProbe, "_inc", "metrics"),
        (probe.LiveRetargetSafetyProbe, "_timing", "metrics"),
    ):
        wrap(owner, name, stage)
    if hasattr(run.probe, "_prepared_adapter"):
        wrap(type(run.probe._prepared_adapter), "adapt", "adapter")
    else:
        wrap(probe, "adapt_rebocap_delta_pose", "adapter")
    if run.probe._pose_observer is not None:
        wrap(run.probe, "_pose_observer", "observer")
    if implementation.session is not None:
        wrap(implementation.session.ControlledMotionSession, "command", "cue_state")
        wrap(implementation.session, "analyze_cue", "cue_analysis")


def _profile_summary(profile, implementation, *, validation_only=False):
    rows = []
    for (filename, line, function), values in pstats.Stats(profile).stats.items():
        source = Path(filename)
        if implementation.root not in source.parents:
            continue
        primitive, calls, own, cumulative, _callers = values
        rows.append(dict(file=source.name, function=function, line=line,
                         primitive_calls=primitive, calls=calls,
                         own_seconds=own, cumulative_seconds=cumulative))
    ordered = sorted(rows, key=lambda row: row["cumulative_seconds"], reverse=True)
    if validation_only:
        return [row for row in ordered if row["function"] in ("normalized", "__post_init__")]
    return ordered[:20]


def benchmark(*, variants=("A",), samples=300, repeats=3, warmup=100,
              diagnostic="none", gc_mode="normal", implementation_root=None,
              implementation_label="current", path="research"):
    if (any(type(n) is not int for n in (samples, repeats, warmup))
            or not 1 <= samples <= 2000 or not 1 <= repeats <= 5 or not 0 <= warmup <= 2000):
        raise ValueError("invalid bounded benchmark size")
    if (not variants or any(v not in VARIANTS for v in variants)
            or len(set(variants)) != len(variants)
            or diagnostic not in ("none", "stages", "cprofile", "allocations", "gc")
            or gc_mode not in ("normal", "on", "off")
            or implementation_label not in ("current", "phase2e", "phase2f-before")):
        raise ValueError("invalid benchmark option")
    if path not in ("research", "production-value") or (path == "production-value"
            and (tuple(variants) != ("A",) or diagnostic == "stages")):
        raise ValueError("production value comparison supports A without stage wrappers")
    implementation = _load_implementation(implementation_root)
    primary = diagnostic == "none" and gc_mode == "normal"
    report = dict(schema="reboretarget.offline-benchmark.v1", implementation=implementation_label,
        python=".".join(map(str, sys.version_info[:3])), fixture="noncommuting_bind_and_sdk_delta_v1",
        path=path, production_path_note="synthetic_value_path_not_product_transport_or_cadence_proof",
        timing="primary_boundary_timing" if primary else "diagnostic_not_acceptance_timing",
        diagnostic=diagnostic, gc_mode=gc_mode, samples_per_repeat=samples, repeats=repeats,
        gc_scope="benchmark_process_only_explicit_mode_restored_no_live_policy_change",
        warmup_per_repeat=warmup, percentile_method="exact_nearest_rank",
        measured_boundary="on_pose_plus_process_latest_including_observer_and_markers",
        threshold_note="exact_pure_samples_preserve_original_live_boundary_but_synthetic_pass_is_not_live_pass",
        primary_overhead="outer_clock_reads_and_post_pure_histogram_sample_retention_included_in_full_frame",
        cpu_note="per_frame_process_cpu_accounting_may_be_quantized_prefer_whole_repeat_totals",
        clocks={name: dict(implementation=time.get_clock_info(name).implementation,
                           resolution_seconds=time.get_clock_info(name).resolution)
                for name in ("perf_counter", "process_time")},
        excludes="episode_setup_warmup_scheduling_sdk_network_audio",
        stages_are_inclusive_and_not_additive=True, variants={},
        pending={"G_supervisor_ipc": "NOT_MEASURED_use_separate_existing_synthetic_integration",
                 "H_countdown_wrapper": "NOT_MEASURED_pending_same_path_synthetic_gate"})
    if path == "production-value":
        report["measured_boundary"] = "validation_delta_adapter_latest_fk_anchors_osc_16_encodes"
        report["excludes"] = "sdk_scheduling_audio_observer_histograms_research_decode_and_addressset_checks"
        report["primary_overhead"] = "outer_clock_reads_only_bytes_equivalence_verified_outside_timing"
    initial_gc = gc.isenabled()
    try:
        if gc_mode == "on":
            gc.enable()
        elif gc_mode == "off":
            gc.disable()
        report["effective_gc_enabled"] = gc.isenabled()
        for variant in variants:
            if implementation.session is None and variant != "A":
                report["variants"][variant] = {"status": "UNAVAILABLE_IN_SNAPSHOT"}
                continue
            runs, combined_wall, combined_cpu, combined_pure = [], [], [], []
            for _ in range(repeats):
                warm = _Run(implementation, variant, path)
                for _ in range(warmup):
                    warm.prepare_frame()
                    warm.step()
                warm.verify(warmup)
                del warm
                run = _Run(implementation, variant, path)
                wall_values, cpu_values = [], []
                recorder = {stage: ([], []) for stage in STAGES}
                profile = cProfile.Profile() if diagnostic == "cprofile" else None
                before_gc = gc.get_stats()
                gc_pauses, gc_started, gc_events = [], {}, [0]
                def on_gc(phase, info):
                    generation = info.get("generation")
                    if generation not in (0, 1, 2):
                        return
                    if phase == "start":
                        gc_started[generation] = time.perf_counter_ns()
                    elif phase == "stop" and generation in gc_started:
                        elapsed = (time.perf_counter_ns() - gc_started.pop(generation)) / 1e6
                        gc_events[0] += 1
                        if len(gc_pauses) < 10000:
                            gc_pauses.append(elapsed)
                repeat_wall_started, repeat_cpu_started = time.perf_counter_ns(), time.process_time_ns()
                with ExitStack() as stack:
                    if diagnostic == "gc":
                        gc.callbacks.append(on_gc)
                        stack.callback(gc.callbacks.remove, on_gc)
                    if diagnostic == "stages":
                        _stage_wrappers(implementation, recorder, stack, run)
                    if diagnostic == "allocations":
                        if tracemalloc.is_tracing():
                            raise ValueError("allocation diagnostic needs exclusive tracing")
                        tracemalloc.start()
                        stack.callback(tracemalloc.stop)
                    for _ in range(samples):
                        # Exclude priming/episode creation from both timing and diagnostics.
                        if diagnostic == "stages":
                            saved_lengths = {k: len(v[0]) for k, v in recorder.items()}
                        run.prepare_frame()
                        if diagnostic == "stages":
                            for key, previous in saved_lengths.items():
                                del recorder[key][0][previous:]
                                del recorder[key][1][previous:]
                        if profile is not None:
                            profile.enable()
                        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
                        run.step()
                        cpu_values.append((time.process_time_ns() - cpu) / 1e6)
                        wall_values.append((time.perf_counter_ns() - wall) / 1e6)
                        if profile is not None:
                            profile.disable()
                    allocation = None
                    if diagnostic == "allocations":
                        current, peak = tracemalloc.get_traced_memory()
                        retained = tracemalloc.take_snapshot().statistics("filename")
                        allocation = {"current_bytes": current, "peak_bytes": peak,
                                      "retained_allocation_count": sum(item.count for item in retained),
                                      "scope": "iterations_episode_setup_final_run_windows_and_timing_lists",
                                      "excludes": "probe_fixture_construction_and_warmup",
                                      "not_total_allocations_or_live_process_memory": True}
                repeat_wall_seconds = (time.perf_counter_ns() - repeat_wall_started) / 1e9
                repeat_cpu_seconds = (time.process_time_ns() - repeat_cpu_started) / 1e9
                evidence = run.verify(samples)
                after_gc = gc.get_stats()
                row = dict(wall=distribution(wall_values), cpu=distribution(cpu_values), evidence=evidence,
                    callback_wall=distribution(run.callback_wall), callback_cpu=distribution(run.callback_cpu),
                    consumer_wall=distribution(run.consumer_wall), consumer_cpu=distribution(run.consumer_cpu),
                    exact_pure_wall=distribution(run.pure_values),
                    whole_repeat_wall_seconds=repeat_wall_seconds,
                    whole_repeat_cpu_seconds=repeat_cpu_seconds,
                    whole_repeat_scope="all_measured_iterations_and_episode_setup_excludes_warmup",
                    gc_delta=[{key: after[key] - before[key] for key in before}
                              for before, after in zip(before_gc, after_gc)])
                if variant == "F":
                    row["analysis_completion_wall"] = distribution(
                        [value for index, value in enumerate(wall_values, 1) if index % 100 == 0])
                    row["noncompletion_wall"] = distribution(
                        [value for index, value in enumerate(wall_values, 1) if index % 100 != 0])
                if diagnostic == "stages":
                    row["stages"] = {name: {"wall": distribution(w), "cpu": distribution(c)}
                                     for name, (w, c) in recorder.items()}
                if profile is not None:
                    row["profile"] = _profile_summary(profile, implementation)
                    row["validation_counters"] = _profile_summary(profile, implementation, validation_only=True)
                if allocation is not None:
                    row["allocations"] = allocation
                if diagnostic == "gc":
                    row["gc_pauses"] = dict(distribution(gc_pauses), observed_events=gc_events[0],
                        overflow_events=gc_events[0] - len(gc_pauses), total_ms=sum(gc_pauses),
                        scope="iterations_and_episode_setup_not_live_causal_attribution")
                runs.append(row)
                combined_wall.extend(wall_values)
                combined_cpu.extend(cpu_values)
                combined_pure.extend(run.pure_values)
            report["variants"][variant] = dict(description=VARIANTS[variant], runs=runs,
                combined_wall=distribution(combined_wall), combined_cpu=distribution(combined_cpu),
                combined_exact_pure_wall=distribution(combined_pure),
                pure_p99_strictly_below_10ms=(distribution(combined_pure)["p99_ms"] < 10
                                              if primary and combined_pure else None),
                wall_p99_strictly_below_10ms=(distribution(combined_wall)["p99_ms"] < 10 if primary else None))
    finally:
        if initial_gc:
            gc.enable()
        else:
            gc.disable()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation-root", type=Path)
    parser.add_argument("--implementation-label", choices=("current", "phase2e", "phase2f-before"), default="current")
    parser.add_argument("--variants", nargs="+", choices=tuple(VARIANTS), default=["A"])
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--diagnostic", choices=("none", "stages", "cprofile", "allocations", "gc"), default="none")
    parser.add_argument("--path", choices=("research", "production-value"), default="research")
    parser.add_argument("--gc-mode", choices=("normal", "on", "off"), default="normal")
    parser.add_argument("--output", type=Path, help="optional aggregate JSON only")
    args = vars(parser.parse_args(argv))
    output = args.pop("output")
    try:
        result = benchmark(**args)
    except (ValueError, TypeError):
        parser.error("benchmark failed its explicit configuration or synthetic validation")
    encoded = json.dumps(result, allow_nan=False, sort_keys=True)
    if output is not None:
        output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
