#!/usr/bin/env python3
"""Research-only, spawn-isolated receive probe with a parent-owned deadline.

The caller must establish the documented Safe Point. No SDK is imported in the
parent. Only a newly spawned child can be terminated; no application is changed.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import threading
import time
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.live_retarget_safety_probe import (
    AbortReason, LiveRetargetSafetyProbe, ProbeConfig, execute_probe,
)

MAX_PACKET_BYTES = 32768
STAGES = frozenset((
    "import_before", "import_after", "import_failed", "construct_before",
    "construct_after", "registration_before", "registration_after", "open_before",
    "open_after", "observe_start", "heartbeat", "pre_close", "close_before",
    "close_after", "complete", "child_error", "result_ready",
))
SAFE_STRINGS = frozenset(reason.value for reason in AbortReason) | frozenset((
    "reboretarget.phase2e.aggregate.v1", "synthetic_value_path_not_avatar",
    "PASS", "FAIL", "UNVERIFIED", "ABORTED", "IN_PROGRESS", "TRIGGERED",
    "NOT_TRIGGERED", "CONFIRMED", "UNVERIFIED / NOT OBSERVED",
    "NORMAL_DEADLINE_NOT_REACHED", "REBOCAP_PROCESS_GUARD", "ONE_CLIENT_INSTANCE",
    "ONE_SUCCESSFUL_OPEN", "ONE_SUCCESSFUL_CLOSE", "MINIMUM_CALLBACK_COUNT",
    "CALLBACK_RATE", "CALLBACK_RATE_RANGE", "CALLBACK_VALUE_PATH_COUNTS",
    "TIMESTAMP_ORDER", "PROCESSED_SEQUENCE_COUNT", "PIPELINE_COUNTS",
    "PURE_PIPELINE_P99", "PURE_PIPELINE_P99_BUDGET", "CONTROLLED_STALE_CLEAR",
    "FINAL_DISCONNECTED_CLEAR", "OBSERVATION_DURATION", "SIXTY_SECOND_MAXIMUM",
))


def _clean_value(value: Any, template: Any) -> Any:
    """Keep only the existing aggregate schema, finite metrics and fixed enums."""
    if isinstance(template, dict):
        if not isinstance(value, dict) or not template.keys() <= value.keys():
            raise ValueError("invalid aggregate")
        return {key: _clean_value(value[key], sample)
                for key, sample in template.items() if key in value}
    if isinstance(template, list):
        if not isinstance(value, list) or len(value) > 64:
            raise ValueError("invalid aggregate")
        return [_clean_value(item, None) for item in value]
    if isinstance(template, str):
        if not isinstance(value, str) or value not in SAFE_STRINGS:
            raise ValueError("invalid aggregate")
        return value
    if isinstance(template, bool) and not isinstance(value, bool):
        raise ValueError("invalid aggregate")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and math.isfinite(value) and abs(value) < 1e15:
        return value
    if isinstance(value, str) and value in SAFE_STRINGS:
        return value
    raise ValueError("invalid aggregate")


def _clean_packet(packet: Any, template: dict) -> dict:
    if not isinstance(packet, dict) or packet.get("stage") not in STAGES:
        raise ValueError("invalid checkpoint")
    elapsed = packet.get("elapsed_seconds", 0.0)
    if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
        raise ValueError("invalid checkpoint time")
    if not math.isfinite(elapsed) or not 0 <= elapsed < 1e9:
        raise ValueError("invalid checkpoint time")
    result = {"stage": packet["stage"], "elapsed_seconds": elapsed}
    if "aggregate" in packet:
        result["aggregate"] = _clean_value(packet["aggregate"], template)
    elif packet["stage"] == "result_ready":
        raise ValueError("missing final aggregate")
    return result


def _load_official_sdk(sdk_root: str) -> Any:
    sys.path.insert(0, sdk_root)
    from rebocap_ws_sdk import rebocap_ws_sdk
    return rebocap_ws_sdk


def _silence_child() -> None:
    # dup2 covers native writes as well as Python output; never forward vendor text.
    sink = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(sink, 1)
        os.dup2(sink, 2)
    finally:
        os.close(sink)
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _child_probe(connection: Any, sdk_root: str, port: int, process_id: int,
                 config_values: dict, sdk_loader: Callable[[str], Any]) -> None:
    _silence_child()
    started = time.perf_counter()
    config = ProbeConfig(**config_values)
    template = LiveRetargetSafetyProbe(config).aggregate_result()

    def progress(packet: dict) -> None:
        packet = dict(packet, elapsed_seconds=time.perf_counter() - started)
        clean = _clean_packet(packet, template)
        data = json.dumps(clean, allow_nan=False, separators=(",", ":")).encode("utf-8")
        if len(data) > MAX_PACKET_BYTES:
            raise ValueError("aggregate too large")
        connection.send_bytes(data)

    def checkpoint(stage: str) -> None:
        progress({"stage": stage, "elapsed_seconds": time.perf_counter() - started})

    try:
        checkpoint("import_before")
        try:
            sdk = sdk_loader(sdk_root)
        except Exception:
            checkpoint("import_failed")
            return
        checkpoint("import_after")
        result = execute_probe(sdk, port=port, process_id=process_id,
                               config=config, progress=progress)
        progress({"stage": "result_ready", "elapsed_seconds": time.perf_counter() - started,
                  "aggregate": result})
    except BaseException:
        try:
            checkpoint("child_error")
        except BaseException:
            pass
    finally:
        connection.close()


def supervise_probe(*, sdk_root: Path, port: int, process_id: int,
                    config: ProbeConfig, hard_timeout_seconds: float = 45.0,
                    _sdk_loader: Callable[[str], Any] = _load_official_sdk) -> dict:
    """Spawn one child, retain latest aggregate, and bound every parent wait.

    Time includes process startup and cleanup; OS scheduling is not hard realtime.
    A reader daemon alone may block on a partial IPC frame, never the controller.
    The private loader seam is only for synthetic tests, not an alternate SDK API.
    """
    if not isinstance(config, ProbeConfig):
        raise ValueError("config must be ProbeConfig")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("port out of range")
    if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id <= 0:
        raise ValueError("process_id must be positive")
    if isinstance(hard_timeout_seconds, bool) or not math.isfinite(hard_timeout_seconds):
        raise ValueError("invalid hard timeout")
    if not config.duration_seconds + 1 <= hard_timeout_seconds <= 60:
        raise ValueError("hard timeout must allow observation plus cleanup and be <= 60")
    sdk_root = Path(sdk_root).resolve()
    if not sdk_root.is_dir():
        raise ValueError("SDK directory is unavailable")
    template = LiveRetargetSafetyProbe(config).aggregate_result()
    context = multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    child = context.Process(target=_child_probe, args=(
        send, str(sdk_root), port, process_id, asdict(config), _sdk_loader), daemon=True)
    # Only the reader writes these references. No child-owned lock is acquired.
    latest: dict = {"packet": None, "aggregate": None, "count": 0, "invalid": 0,
                   "received_at": None}
    reader_done = threading.Event()

    def read_progress() -> None:
        try:
            while True:
                try:
                    packet = _clean_packet(json.loads(receive.recv_bytes(MAX_PACKET_BYTES)), template)
                except (ValueError, UnicodeError, json.JSONDecodeError):
                    latest["invalid"] += 1
                    continue
                latest["packet"] = packet
                latest["received_at"] = time.perf_counter()
                if "aggregate" in packet:
                    latest["aggregate"] = packet["aggregate"]
                latest["count"] += 1
        except (EOFError, OSError):
            pass
        finally:
            reader_done.set()

    started = time.perf_counter()
    deadline = started + hard_timeout_seconds
    # Reserve one second for terminate, exit observation, and report collection.
    stop_at = deadline - 1.0
    reason, termination_requested = "CHILD_EXIT", False
    termination_error = False
    try:
        child.start()
        send.close()
        threading.Thread(target=read_progress, daemon=True).start()
        while child.is_alive() and time.perf_counter() < stop_at:
            child.join(min(0.025, max(0.0, stop_at - time.perf_counter())))
        if child.is_alive():
            reason, termination_requested = "DEADLINE", True
            try:
                child.terminate()
            except (OSError, PermissionError):
                termination_error = True
            child.join(max(0.0, deadline - time.perf_counter() - 0.05))
        reader_done.wait(max(0.0, min(0.05, deadline - time.perf_counter())))
    except BaseException:
        # Includes user interruption: never abandon the SDK child or wait forever.
        reason = "SPAWN_OR_SUPERVISION_ERROR"
    finally:
        if child.pid is not None and child.is_alive():
            termination_requested = True
            try:
                child.terminate()
            except (OSError, PermissionError):
                termination_error = True
            child.join(max(0.0, deadline - time.perf_counter() - 0.05))
        send.close()
    ended = time.perf_counter()
    alive = child.is_alive() if child.pid is not None else False
    packet, aggregate = latest["packet"], latest["aggregate"]
    complete = packet is not None and packet["stage"] == "result_ready"
    clean_exit = (complete and isinstance(aggregate, dict) and not alive and child.exitcode == 0
                  and not termination_requested and not termination_error
                  and not latest["invalid"] and ended <= deadline
                  and reason == "CHILD_EXIT")
    status = aggregate.get("status", "UNVERIFIED") if clean_exit else "UNVERIFIED"
    report = {
        "schema": "reboretarget.phase2e.supervisor.v1", "status": status,
        "supervisor_reason": reason, "start_perf_counter": started,
        "deadline_perf_counter": deadline, "end_perf_counter": ended,
        "elapsed_seconds": ended - started, "hard_timeout_seconds": hard_timeout_seconds,
        "within_deadline": ended <= deadline, "child_pid": child.pid,
        "child_exit_code": child.exitcode, "child_exit_observed": not alive,
        "termination_requested": termination_requested, "termination_error": termination_error,
        "latest_checkpoint": packet, "aggregate": aggregate, "result_ready": complete,
        "checkpoint_count": latest["count"], "invalid_packet_count": latest["invalid"],
        "last_progress_age_seconds": (ended - latest["received_at"]
                                      if latest["received_at"] is not None else None),
        "reconnect_attempts": 0,
    }
    if not alive:
        child.close()
    # Do not close a pipe in another thread blocked in native recv; it is daemon-only.
    if reader_done.is_set():
        receive.close()
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--process-id", type=int, required=True)
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--hard-timeout-seconds", type=float, default=45.0)
    parser.add_argument("--stale-after-seconds", type=float, default=0.250)
    parser.add_argument("--quaternion-norm-tolerance", type=float, default=1e-4)
    parser.add_argument("--consumer-hz", type=float, default=30.0)
    parser.add_argument("--pure-pipeline-p99-budget-ms", type=float, default=10.0)
    args = parser.parse_args(argv)
    def cancel(_signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, cancel)
    signal.signal(signal.SIGTERM, cancel)
    try:
        config = ProbeConfig(duration_seconds=args.duration_seconds,
            stale_after_seconds=args.stale_after_seconds,
            quaternion_norm_tolerance=args.quaternion_norm_tolerance,
            consumer_hz=args.consumer_hz,
            pure_pipeline_p99_budget_ms=args.pure_pipeline_p99_budget_ms)
        report = supervise_probe(sdk_root=args.sdk_root, port=args.port,
            process_id=args.process_id, config=config, hard_timeout_seconds=args.hard_timeout_seconds)
    except (TypeError, ValueError):
        parser.error("invalid explicit probe configuration")
    print("RESULT_JSON=" + json.dumps(report, allow_nan=False, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    # Avoid multiprocessing's implicit unbounded atexit join if OS termination failed.
    os._exit(main())
