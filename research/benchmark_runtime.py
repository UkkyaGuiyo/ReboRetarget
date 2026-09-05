"""Bounded synthetic supervisor comparisons; no vendor SDK, audio or output send.

G0 omits progress aggregation, G1 retains it but discards progress packets, G2
uses normal IPC. All retain the same supervisor and final result path. H runs
the existing countdown wrapper with silent synthetic speech, not a real speaker.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from functools import partial
import importlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

STAGES = ("callback", "consumer", "wait_actual", "wait_requested", "aggregate", "progress")
FIELDS = ("count", "mean_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms")
EXTRAS = ("child_cpu_seconds", "child_wall_seconds", "progress_calls", "scheduled_input_skips")
TELEMETRY_SIZE = len(STAGES)*len(FIELDS) + len(EXTRAS)


def _distribution(values):
    values = sorted(values)
    def percentile(fraction):
        return values[max(0, math.ceil(len(values)*fraction)-1)] if values else 0.
    return dict(count=len(values), mean_ms=sum(values)/len(values) if values else 0.,
                p50_ms=percentile(.5), p95_ms=percentile(.95), p99_ms=percentile(.99),
                max_ms=max(values) if values else 0.)


def _load(root):
    root = Path(root).resolve()
    checked = ("research.live_retarget_safety_probe", "research.supervised_retarget_probe",
               "reboretarget.fk", "tests.synthetic_fixtures")
    for name in checked:
        existing = sys.modules.get(name)
        if existing is not None and root not in Path(existing.__file__).resolve().parents:
            raise ValueError("fresh process required for another implementation")
    if not (root/"research"/"supervised_retarget_probe.py").is_file():
        raise ValueError("implementation snapshot unavailable")
    sys.path.insert(0, str(root))
    probe = importlib.import_module("research.live_retarget_safety_probe")
    supervisor = importlib.import_module("research.supervised_retarget_probe")
    for name in checked:
        module = sys.modules.get(name)
        if module is not None and root not in Path(module.__file__).resolve().parents:
            raise ValueError("mixed implementation snapshot")
    return probe, supervisor


class _SyntheticSdk:
    def __init__(self, counters, **options):
        if options != dict(coordinate_type="synthetic_unity", use_global_rotation=True):
            raise ValueError("unexpected fake SDK configuration")
        self.counters, self.stop, self.worker = counters, threading.Event(), None
    def set_pose_msg_callback(self, callback):
        self.callback = callback
    def set_exception_close_callback(self, callback):
        self.close_callback = callback
    def open(self, port):
        if port != 7690:
            raise ValueError("unexpected fake port")
        def produce():
            sequence, due = 0, time.perf_counter()
            while not self.stop.is_set():
                remaining = due-time.perf_counter()
                if remaining > 0 and self.stop.wait(remaining):
                    break
                self.callback(self, (0.,1.,0.), ((1.,0.,0.,0.),)*24, -1, sequence/60.)
                sequence += 1
                due += 1/60
                now = time.perf_counter()
                if now-due > 1/60:
                    skipped = int((now-due)*60)
                    self.counters["scheduled_input_skips"] += skipped
                    due += skipped/60
        self.worker = threading.Thread(target=produce, daemon=True)
        self.worker.start()
        return 0
    def close(self):
        self.stop.set()
        if self.worker is not None:
            self.worker.join(.5)


def _synthetic_loader(_path, *, root, mode, telemetry):
    probe, supervisor = _load(root)
    original_execute = supervisor.execute_probe
    counters = {"progress_calls": 0, "scheduled_input_skips": 0}
    def execute(sdk, **kwargs):
        samples = {name: [] for name in STAGES}
        def record(stage, elapsed):
            if len(samples[stage]) < 8192:
                samples[stage].append(elapsed*1000)
        progress = kwargs.get("progress")
        def measured_progress(packet):
            started = time.perf_counter()
            counters["progress_calls"] += 1
            try:
                if mode != "G1" and progress is not None:
                    progress(packet)
            finally:
                record("progress", time.perf_counter()-started)
        kwargs["progress"] = None if mode == "G0" else measured_progress
        original_wait = kwargs.get("waiter", probe._default_wait)
        def measured_wait(event, timeout):
            started = time.perf_counter()
            original_wait(event, timeout)
            record("wait_requested", timeout)
            record("wait_actual", time.perf_counter()-started)
        kwargs["waiter"] = measured_wait
        wall, cpu = time.perf_counter(), time.process_time()
        try:
            with ExitStack() as stack:
                for name, stage in (("on_pose", "callback"), ("process_latest", "consumer"),
                                    ("aggregate_result", "aggregate")):
                    original = getattr(probe.LiveRetargetSafetyProbe, name)
                    def measured(self, *args, _original=original, _stage=stage, **keywords):
                        started = time.perf_counter()
                        try:
                            return _original(self, *args, **keywords)
                        finally:
                            record(_stage, time.perf_counter()-started)
                    stack.enter_context(patch.object(probe.LiveRetargetSafetyProbe, name, measured))
                return original_execute(sdk, **kwargs)
        finally:
            extras = dict(child_cpu_seconds=time.process_time()-cpu,
                          child_wall_seconds=time.perf_counter()-wall, **counters)
            for index, stage in enumerate(STAGES):
                summary = _distribution(samples[stage])
                for offset, field in enumerate(FIELDS):
                    telemetry[index*len(FIELDS)+offset] = summary[field]
            for index, name in enumerate(EXTRAS):
                telemetry[len(STAGES)*len(FIELDS)+index] = extras[name]
    supervisor.execute_probe = execute
    return SimpleNamespace(CoordinateType=SimpleNamespace(UnityCoordinate="synthetic_unity"),
                           RebocapWsSdk=partial(_SyntheticSdk, counters))


class _SilentJob:
    def __init__(self, *_args):
        self.cancelled = False
    def poll(self):
        return 0
    def cancel(self):
        self.cancelled = True
    def close(self, _timeout):
        self.cancel()
        return True


def _safe_row(report, telemetry, parent_cpu, parent_wall):
    aggregate = report.get("aggregate")
    if not isinstance(aggregate, dict) or not report.get("child_exit_observed"):
        raise ValueError("synthetic child result unavailable")
    counts = aggregate["counts"]
    processed, accepted = counts["processed_unique_sequences"], counts["publish_accepted"]
    if (accepted <= 0 or processed <= 0 or aggregate["abort_reason"] != "NONE"
            or counts["pipeline_successes"] != processed
            or counts["decoded_messages"] != processed*16
            or counts["canonical_pose_created"] != accepted
            or counts["delta_pose_created"] != accepted):
        raise ValueError("synthetic value path failed")
    extras = {name: telemetry[len(STAGES)*len(FIELDS)+i] for i, name in enumerate(EXTRAS)}
    duration = aggregate["lifecycle"]["observation_duration_seconds"]
    return dict(status=report["status"], clean_child_exit=report["child_exit_code"] == 0,
        within_deadline=report["within_deadline"], forced_termination=report["termination_requested"],
        configured_consumer_hz=aggregate["configuration"]["consumer_hz"],
        observed_callback_hz=aggregate["callback_rate"]["average_hz"],
        observed_consumer_hz=processed/duration if duration else None,
        observation_seconds=duration, parent_total_wall_seconds=parent_wall,
        parent_cpu_seconds=parent_cpu, **extras,
        child_cpu_ms_per_processed=extras["child_cpu_seconds"]*1000/processed,
        parent_cpu_ms_per_processed=parent_cpu*1000/processed,
        counts={name: counts[name] for name in ("callbacks_received", "publish_accepted",
            "processed_unique_sequences", "sequence_gap_drops", "decoded_messages")},
        stage_wall_exact_nearest_rank={stage: {field: telemetry[i*len(FIELDS)+j]
            for j, field in enumerate(FIELDS)} for i, stage in enumerate(STAGES)},
        core_histogram_lower_edge_ms={name: aggregate["timings_ms"][name]
            for name in ("pure_pipeline", "receive_to_decode", "receive_interval")},
        checkpoint_count=report["checkpoint_count"], invalid_packets=report["invalid_packet_count"])


def benchmark(*, modes=("G0", "G1", "G2"), duration=5., repeats=1, consumer_rates=(30.,60.),
              implementation_root=None, implementation_label="current"):
    if (not modes or len(set(modes)) != len(modes) or any(mode not in ("G0","G1","G2","H") for mode in modes)
            or type(repeats) is not int or not 1 <= repeats <= 3
            or type(duration) not in (float,int) or not math.isfinite(duration) or not 1 <= duration <= 20
            or not consumer_rates or any(rate not in (30.,60.) for rate in consumer_rates)
            or implementation_label not in ("current", "phase2e", "phase2f-before")):
        raise ValueError("invalid bounded runtime benchmark")
    root = Path(implementation_root or Path(__file__).resolve().parents[1]).resolve()
    probe, supervisor = _load(root)
    rows = []
    for mode in modes:
        rates = (30.,) if mode == "H" else consumer_rates
        for rate in rates:
            for repeat in range(repeats):
                telemetry = multiprocessing.get_context("spawn").RawArray("d", TELEMETRY_SIZE)
                loader = partial(_synthetic_loader, root=str(root), mode=mode, telemetry=telemetry)
                start, cpu = time.perf_counter(), time.process_time()
                if mode == "H":
                    if not (root/"research"/"countdown_motion_cue.py").is_file():
                        rows.append(dict(mode=mode, repeat=repeat, status="UNAVAILABLE_IN_SNAPSHOT"))
                        continue
                    countdown = importlib.import_module("research.countdown_motion_cue")
                    result = countdown.run_countdown(sdk_root=root, port=7690, process_id=os.getpid(),
                        cue="right", user_ready=True, _sdk_loader=loader, _speech_factory=_SilentJob)
                else:
                    result = supervisor.supervise_probe(sdk_root=root, port=7690, process_id=os.getpid(),
                        config=probe.ProbeConfig(duration_seconds=duration, consumer_hz=rate),
                        hard_timeout_seconds=min(60., duration+5), _sdk_loader=loader)
                row = _safe_row(result, telemetry, time.process_time()-cpu, time.perf_counter()-start)
                row.update(mode=mode, repeat=repeat)
                if mode == "H":
                    row["motion_counts"] = result["motion"]["counts"]
                    row["motion_state"] = result["motion"]["state"]
                    row["wrapper_total_including_cleanup_seconds"] = result["total_elapsed_seconds_including_audio_cleanup"]
                    row["countdown_error"] = result["countdown"]["error"]
                rows.append(row)
    return dict(schema="reboretarget.synthetic-runtime-benchmark.v1", implementation=implementation_label,
        python=".".join(map(str,sys.version_info[:3])), source="synthetic_constant_pose_60hz_no_backlog_producer",
        timing="balanced_outer_wall_wrappers_not_uninstrumented_live_acceptance",
        groups=dict(G0="no_progress_aggregation", G1="aggregate_kept_progress_discarded",
                    G2="normal_progress_ipc", H="exact_countdown_wrapper_silent_poll_job"),
        comparison="G1-minus-G0 aggregation; G2-minus-G1 clean_JSON_Pipe_reader; no direct-vs-supervised conflation",
        privacy="aggregate_only_no_paths_PIDs_source_timestamps_or_motion_values",
        caveats=["outer_consumer_includes_empty_snapshots_and_observer",
                 "core_histogram_percentiles_are_lower_edges_not_exact_outer_quantiles",
                 "parent_and_child_CPU_are_separate; audio_process_CPU_is_not_measured",
                 "short_runs_can_quantize_Windows_process_CPU_to_zero",
                 "H_silent_job_does_not_measure_SystemSpeech_or_audibility",
                 "warmup_startup_and_low_sample_quantiles_require_separate_interpretation"], rows=rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation-root", type=Path)
    parser.add_argument("--implementation-label", choices=("current","phase2e","phase2f-before"), default="current")
    parser.add_argument("--modes", choices=("G0","G1","G2","H"), nargs="+", default=["G0","G1","G2"])
    parser.add_argument("--duration", type=float, default=5.)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--consumer-rates", type=float, choices=(30.,60.), nargs="+", default=[30.,60.])
    args = vars(parser.parse_args(argv))
    try:
        report = benchmark(**args)
    except (TypeError,ValueError):
        parser.error("synthetic runtime benchmark configuration or value path failed")
    print(json.dumps(report,allow_nan=False,sort_keys=True),flush=True)
    return 0


if __name__ == "__main__":
    os._exit(main())
