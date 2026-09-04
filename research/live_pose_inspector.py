#!/usr/bin/env python3
"""Read-only aggregate observer for the official ReboCap WebSocket SDK.

This research tool never sends OSC, changes ReboCap settings, or records raw
poses. It writes only aggregate timing and joint-activity statistics.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import signal
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


JOINT_NAMES = (
    "Pelvis", "L_Hip", "R_Hip", "Spine1", "L_Knee", "R_Knee",
    "Spine2", "L_Ankle", "R_Ankle", "Spine3", "L_Foot", "R_Foot",
    "Neck", "L_Collar", "R_Collar", "Head", "L_Shoulder",
    "R_Shoulder", "L_Elbow", "R_Elbow", "L_Wrist", "R_Wrist",
    "L_Hand", "R_Hand",
)
YAW_JOINTS = {0, 3, 6, 9}
ANGLE_ACTIVE_DEG = 0.25


class Histogram:
    """Fixed-size histogram for bounded-memory percentile estimates."""

    def __init__(self, width: float, maximum: float) -> None:
        self.width = width
        self.maximum = maximum
        self.bins = [0] * (math.ceil(maximum / width) + 1)
        self.overflow = 0
        self.count = 0
        self.total = 0.0
        self.minimum = math.inf
        self.maximum_seen = -math.inf

    def add(self, value: float) -> None:
        if not math.isfinite(value):
            return
        self.count += 1
        self.total += value
        self.minimum = min(self.minimum, value)
        self.maximum_seen = max(self.maximum_seen, value)
        if value < 0 or value > self.maximum:
            self.overflow += 1
            return
        self.bins[min(int(value / self.width), len(self.bins) - 1)] += 1

    def percentile(self, fraction: float) -> float | None:
        if not self.count:
            return None
        target = max(1, math.ceil(self.count * fraction))
        seen = 0
        for index, amount in enumerate(self.bins):
            seen += amount
            if seen >= target:
                return round(index * self.width, 4)
        return round(self.maximum_seen, 4)

    def summary(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.total / self.count, 6) if self.count else None,
            "min": round(self.minimum, 6) if self.count else None,
            "median": self.percentile(0.50),
            "p95": self.percentile(0.95),
            "p99": self.percentile(0.99),
            "max": round(self.maximum_seen, 6) if self.count else None,
            "overflow_count": self.overflow,
        }


@dataclass
class JointStats:
    samples: int = 0
    invalid: int = 0
    norm_total: float = 0.0
    norm_error_max: float = 0.0
    active_count: int = 0
    previous: tuple[float, float, float, float] | None = None
    angular_delta: Histogram = field(default_factory=lambda: Histogram(0.1, 180.0))

    def add(self, quat: Iterable[float]) -> None:
        try:
            q = tuple(float(value) for value in quat)
        except (TypeError, ValueError):
            self.invalid += 1
            return
        if len(q) != 4 or not all(math.isfinite(value) for value in q):
            self.invalid += 1
            return
        norm = math.sqrt(sum(value * value for value in q))
        if norm <= 1e-9:
            self.invalid += 1
            return
        normalized = tuple(value / norm for value in q)
        self.samples += 1
        self.norm_total += norm
        self.norm_error_max = max(self.norm_error_max, abs(norm - 1.0))
        if self.previous is not None:
            dot = min(1.0, abs(sum(a * b for a, b in zip(self.previous, normalized))))
            delta = math.degrees(2.0 * math.acos(dot))
            self.angular_delta.add(delta)
            if delta >= ANGLE_ACTIVE_DEG:
                self.active_count += 1
        self.previous = normalized

    def summary(self) -> dict[str, Any]:
        deltas = self.angular_delta.summary()
        return {
            "samples": self.samples,
            "invalid": self.invalid,
            "quaternion_norm_mean": round(self.norm_total / self.samples, 7) if self.samples else None,
            "quaternion_norm_max_abs_error": round(self.norm_error_max, 7) if self.samples else None,
            "angular_delta_deg": deltas,
            "active_fraction_ge_0_25deg": (
                round(self.active_count / deltas["count"], 6) if deltas["count"] else None
            ),
        }


@dataclass
class YawStats:
    samples: int = 0
    previous_wrapped: float | None = None
    unwrapped: float = 0.0
    start: float | None = None
    minimum: float = math.inf
    maximum: float = -math.inf
    jumps_over_30deg: int = 0

    def add(self, q: Iterable[float]) -> None:
        try:
            values = tuple(float(value) for value in q)
        except (TypeError, ValueError):
            return
        if len(values) != 4 or not all(math.isfinite(value) for value in values):
            return
        w, x, y, z = values
        norm = math.sqrt(w * w + x * x + y * y + z * z)
        if norm <= 1e-9:
            return
        w, x, y, z = w / norm, x / norm, y / norm, z / norm
        forward_x = 2.0 * (x * z + w * y)
        forward_z = 1.0 - 2.0 * (x * x + y * y)
        wrapped = math.degrees(math.atan2(forward_x, forward_z))
        if self.previous_wrapped is None:
            self.unwrapped = wrapped
            self.start = wrapped
        else:
            delta = (wrapped - self.previous_wrapped + 180.0) % 360.0 - 180.0
            if abs(delta) > 30.0:
                self.jumps_over_30deg += 1
            self.unwrapped += delta
        self.previous_wrapped = wrapped
        self.samples += 1
        self.minimum = min(self.minimum, self.unwrapped)
        self.maximum = max(self.maximum, self.unwrapped)

    def summary(self) -> dict[str, Any]:
        return {
            "samples": self.samples,
            "start_deg": round(self.start, 4) if self.start is not None else None,
            "end_deg": round(self.unwrapped, 4) if self.samples else None,
            "net_change_deg": round(self.unwrapped - self.start, 4) if self.start is not None else None,
            "range_deg": round(self.maximum - self.minimum, 4) if self.samples else None,
            "single_frame_jumps_over_30deg": self.jumps_over_30deg,
            "interpretation": "Unity-coordinate forward-vector yaw proxy; normal turning is not drift.",
        }


class Metrics:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.started_utc = datetime.now(timezone.utc)
        self.first_receive_monotonic: float | None = None
        self.last_receive_monotonic: float | None = None
        self.first_source_ts: float | None = None
        self.last_source_ts: float | None = None
        self.callback_count = 0
        self.invalid_frames = 0
        self.joint_counts: Counter[int] = Counter()
        self.static_indexes: Counter[int] = Counter()
        self.receive_intervals_ms = Histogram(0.1, 200.0)
        self.source_intervals_ms = Histogram(0.1, 200.0)
        self.clock_offset_ms = Histogram(0.1, 2000.0)
        self.clock_residual_ms = Histogram(0.1, 2000.0)
        self.first_clock_offset: float | None = None
        self.timestamp_non_monotonic = 0
        self.timestamp_jumps_over_250ms = 0
        self.gaps = {50: 0, 100: 0, 250: 0, 1000: 0}
        self.burst_intervals_under_4ms = 0
        self.backlog_candidates = 0
        self.fast_run_after_gap = 0
        self.root_min = [math.inf] * 3
        self.root_max = [-math.inf] * 3
        self.root_step_max = 0.0
        self.previous_root: tuple[float, float, float] | None = None
        self.joints = [JointStats() for _ in JOINT_NAMES]
        self.yaw = {index: YawStats() for index in YAW_JOINTS}
        self.open_attempts = 0
        self.open_successes = 0
        self.disconnects = 0
        self.reconnects = 0
        self.currently_connected = False
        self.stale_since_monotonic: float | None = None

    def mark_open_attempt(self) -> None:
        with self.lock:
            self.open_attempts += 1

    def mark_connected(self) -> None:
        with self.lock:
            if self.open_successes:
                self.reconnects += 1
            self.open_successes += 1
            self.currently_connected = True
            self.stale_since_monotonic = None

    def mark_disconnected(self) -> None:
        with self.lock:
            if self.currently_connected:
                self.disconnects += 1
            self.currently_connected = False
            self.stale_since_monotonic = time.perf_counter()

    def add_pose(self, trans: Any, pose24: Any, static_index: Any, source_ts: Any) -> None:
        receive_mono = time.perf_counter()
        receive_epoch = time.time()
        with self.lock:
            try:
                source = float(source_ts)
                root = tuple(float(value) for value in trans)
                poses = tuple(tuple(float(value) for value in quat) for quat in pose24)
                static = int(static_index)
            except (TypeError, ValueError):
                self.invalid_frames += 1
                return

            self.callback_count += 1
            self.joint_counts[len(poses)] += 1
            self.static_indexes[static] += 1
            self.currently_connected = True
            self.stale_since_monotonic = None

            if self.first_receive_monotonic is None:
                self.first_receive_monotonic = receive_mono
                self.first_source_ts = source
                self.first_clock_offset = receive_epoch - source
            if self.last_receive_monotonic is not None:
                interval_ms = (receive_mono - self.last_receive_monotonic) * 1000.0
                self.receive_intervals_ms.add(interval_ms)
                for threshold in self.gaps:
                    if interval_ms >= threshold:
                        self.gaps[threshold] += 1
                if interval_ms < 4.0:
                    self.burst_intervals_under_4ms += 1
                    if self.fast_run_after_gap:
                        self.fast_run_after_gap += 1
                        if self.fast_run_after_gap == 4:
                            self.backlog_candidates += 1
                elif interval_ms >= 50.0:
                    self.fast_run_after_gap = 1
                else:
                    self.fast_run_after_gap = 0
            if self.last_source_ts is not None:
                source_delta_ms = (source - self.last_source_ts) * 1000.0
                self.source_intervals_ms.add(source_delta_ms)
                if source_delta_ms <= 0:
                    self.timestamp_non_monotonic += 1
                if source_delta_ms >= 250.0:
                    self.timestamp_jumps_over_250ms += 1

            if self.first_clock_offset is not None:
                offset = receive_epoch - source
                self.clock_offset_ms.add(abs(offset) * 1000.0)
                self.clock_residual_ms.add(abs(offset - self.first_clock_offset) * 1000.0)

            self.last_receive_monotonic = receive_mono
            self.last_source_ts = source

            if len(root) == 3 and all(math.isfinite(value) for value in root):
                for axis in range(3):
                    self.root_min[axis] = min(self.root_min[axis], root[axis])
                    self.root_max[axis] = max(self.root_max[axis], root[axis])
                if self.previous_root is not None:
                    step = math.sqrt(sum((a - b) ** 2 for a, b in zip(root, self.previous_root)))
                    self.root_step_max = max(self.root_step_max, step)
                self.previous_root = root
            else:
                self.invalid_frames += 1

            if len(poses) != len(JOINT_NAMES):
                self.invalid_frames += 1
                return
            for index, quat in enumerate(poses):
                self.joints[index].add(quat)
                if index in self.yaw:
                    self.yaw[index].add(quat)

    def elapsed(self) -> float:
        with self.lock:
            if self.first_receive_monotonic is None:
                return 0.0
            end = self.last_receive_monotonic or time.perf_counter()
            return max(0.0, end - self.first_receive_monotonic)

    def snapshot(self, final: bool = False) -> dict[str, Any]:
        with self.lock:
            duration = 0.0
            if self.first_receive_monotonic is not None:
                duration = max(0.0, (self.last_receive_monotonic or time.perf_counter()) - self.first_receive_monotonic)
            interval = self.receive_intervals_ms.summary()
            source_interval = self.source_intervals_ms.summary()
            average_hz = ((self.callback_count - 1) / duration) if duration > 0 and self.callback_count > 1 else None
            median_hz = (1000.0 / interval["median"]) if interval["median"] else None
            root_valid = self.previous_root is not None
            result = {
                "schema": 1,
                "final": final,
                "started_utc": self.started_utc.isoformat(),
                "ended_utc": datetime.now(timezone.utc).isoformat() if final else None,
                "connection": {
                    "open_attempts": self.open_attempts,
                    "open_successes": self.open_successes,
                    "disconnects": self.disconnects,
                    "reconnects": self.reconnects,
                    "currently_connected": self.currently_connected,
                    "pose_state": "VALID" if self.currently_connected and self.callback_count else "STALE_OR_INVALID",
                },
                "callback": {
                    "count": self.callback_count,
                    "observed_duration_seconds": round(duration, 3),
                    "average_hz": round(average_hz, 4) if average_hz else None,
                    "median_hz": round(median_hz, 4) if median_hz else None,
                    "receive_interval_ms": interval,
                    "gaps_ge_ms": {str(key): value for key, value in self.gaps.items()},
                    "burst_intervals_under_4ms": self.burst_intervals_under_4ms,
                    "backlog_candidate_runs": self.backlog_candidates,
                },
                "timestamp": {
                    "source_first": self.first_source_ts,
                    "source_last": self.last_source_ts,
                    "source_interval_ms": source_interval,
                    "non_monotonic_deltas": self.timestamp_non_monotonic,
                    "jumps_ge_250ms": self.timestamp_jumps_over_250ms,
                    "receive_minus_source_abs_ms": self.clock_offset_ms.summary(),
                    "offset_change_from_first_abs_ms": self.clock_residual_ms.summary(),
                    "note": "Absolute age is meaningful only if source timestamp shares the Unix clock; residual shows clock/transport drift.",
                },
                "pose": {
                    "invalid_frames": self.invalid_frames,
                    "joint_count_histogram": dict(sorted(self.joint_counts.items())),
                    "static_index_histogram": dict(sorted(self.static_indexes.items())),
                    "pelvis_translation_m": {
                        "min_xyz": [round(value, 6) for value in self.root_min] if root_valid else None,
                        "max_xyz": [round(value, 6) for value in self.root_max] if root_valid else None,
                        "range_xyz": [round(high - low, 6) for low, high in zip(self.root_min, self.root_max)] if root_valid else None,
                        "max_single_frame_step": round(self.root_step_max, 6) if root_valid else None,
                    },
                    "joints": {name: self.joints[index].summary() for index, name in enumerate(JOINT_NAMES)},
                    "yaw_proxy": {JOINT_NAMES[index]: stats.summary() for index, stats in self.yaw.items()},
                },
                "privacy": {
                    "raw_pose_frames_saved": 0,
                    "output_contains_aggregates_only": True,
                },
            }
            return result


def process_alive(process_id: int | None) -> bool:
    if process_id is None or sys.platform != "win32":
        return True
    synchronize = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, process_id)
    if not handle:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 0x00000102
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True, help="Directory containing the official rebocap_ws_sdk package")
    parser.add_argument("--port", type=int, required=True, help="Confirmed ReboCap WebSocket port; no scanning is performed")
    parser.add_argument("--process-id", type=int, help="Exit when this ReboCap process ends")
    parser.add_argument("--output", type=Path, required=True, help="Aggregate JSON output path")
    parser.add_argument("--summary-seconds", type=float, default=30.0)
    args = parser.parse_args()
    if not math.isfinite(args.summary_seconds) or args.summary_seconds < 1.0:
        parser.error("--summary-seconds must be at least 1.0")
    if args.output.exists():
        parser.error("--output must name a new file")
    return args


def main() -> int:
    args = parse_args()
    sys.path.insert(0, str(args.sdk_root.resolve()))
    try:
        from rebocap_ws_sdk import rebocap_ws_sdk
    except Exception as error:
        print(f"SDK import failed: {error}", flush=True)
        return 2

    metrics = Metrics()
    stop = threading.Event()
    disconnected = threading.Event()
    sdk_holder: list[Any] = []

    def request_stop(_signum: int, _frame: Any) -> None:
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    def on_pose(_sdk: Any, trans: Any, pose24: Any, static_index: Any, timestamp: Any) -> None:
        try:
            metrics.add_pose(trans, pose24, static_index, timestamp)
        except Exception:
            # Never let malformed external data escape through the native SDK
            # callback boundary. A bad frame is invalid, not process-fatal.
            with metrics.lock:
                metrics.invalid_frames += 1

    def on_close(_sdk: Any) -> None:
        metrics.mark_disconnected()
        disconnected.set()

    last_summary = 0.0
    exit_code = 0
    try:
        if not stop.is_set() and process_alive(args.process_id):
            metrics.mark_open_attempt()
            sdk = rebocap_ws_sdk.RebocapWsSdk(
                coordinate_type=rebocap_ws_sdk.CoordinateType.UnityCoordinate,
                use_global_rotation=True,
            )
            sdk_holder[:] = [sdk]
            sdk.set_pose_msg_callback(on_pose)
            sdk.set_exception_close_callback(on_close)
            result = sdk.open(args.port)
            if result != 0:
                metrics.mark_disconnected()
                print(f"Connect failed with SDK code {result}; no retry was attempted.", flush=True)
                sdk.close()
                sdk_holder.clear()
                exit_code = 3
            else:
                if not disconnected.is_set():
                    metrics.mark_connected()
                    if disconnected.is_set():
                        metrics.mark_disconnected()
                    else:
                        print(f"Connected read-only on port {args.port}; raw poses are not saved.", flush=True)
                        while not stop.is_set() and process_alive(args.process_id) and not disconnected.is_set():
                            now = time.monotonic()
                            if now - last_summary >= args.summary_seconds:
                                snapshot = metrics.snapshot()
                                callback = snapshot["callback"]
                                print(
                                    "Summary "
                                    f"duration={callback['observed_duration_seconds']:.1f}s "
                                    f"frames={callback['count']} "
                                    f"avg={callback['average_hz'] or 0:.2f}Hz "
                                    f"p95={callback['receive_interval_ms']['p95'] or 0:.1f}ms "
                                    f"gaps50={callback['gaps_ge_ms']['50']} "
                                    f"backlog={callback['backlog_candidate_runs']} "
                                    f"state={snapshot['connection']['pose_state']}",
                                    flush=True,
                                )
                                write_json(args.output, snapshot)
                                last_summary = now
                            stop.wait(0.25)

                metrics.mark_disconnected()
                sdk.close()
                sdk_holder.clear()
                if disconnected.is_set() and not stop.is_set():
                    print("Connection lost: Pose is STALE_OR_INVALID; no reconnect was attempted.", flush=True)

    except KeyboardInterrupt:
        stop.set()
    except Exception as error:
        print(f"Inspector error: {error}", flush=True)
        exit_code = 1
    finally:
        if sdk_holder:
            try:
                sdk_holder[0].close()
            except Exception:
                pass
        metrics.mark_disconnected()
        final = metrics.snapshot(final=True)
        write_json(args.output, final)
        callback = final["callback"]
        print(
            "Final "
            f"duration={callback['observed_duration_seconds']:.1f}s "
            f"frames={callback['count']} "
            f"avg={callback['average_hz'] or 0:.2f}Hz "
            f"output={args.output}",
            flush=True,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
