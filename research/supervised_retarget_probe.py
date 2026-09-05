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
import queue
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
    "motion_state",
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


def _clean_packet(packet: Any, template: dict, motion_cue: Optional[str] = None) -> dict:
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
    if "motion" in packet:
        if motion_cue is None or packet["stage"] != "motion_state":
            raise ValueError("unexpected motion status")
        from research.controlled_motion_session import clean_session_status
        result["motion"] = clean_session_status(packet["motion"], motion_cue)
    elif packet["stage"] == "motion_state":
        raise ValueError("missing motion status")
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
                 config_values: dict, sdk_loader: Callable[[str], Any],
                 motion_cue: Optional[str] = None, controls: Any = None) -> None:
    _silence_child()
    started = time.perf_counter()
    config = ProbeConfig(**config_values)
    template = LiveRetargetSafetyProbe(config).aggregate_result()

    def progress(packet: dict) -> None:
        packet = dict(packet, elapsed_seconds=time.perf_counter() - started)
        clean = _clean_packet(packet, template, motion_cue)
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
        session = None
        if motion_cue is not None:
            from research.controlled_motion_session import ControlledMotionSession
            from tests.synthetic_fixtures import synthetic_human_skeleton
            def motion_status(status: dict) -> None:
                progress({"stage": "motion_state", "motion": status})
            session = ControlledMotionSession(motion_cue, synthetic_human_skeleton(),
                started=time.perf_counter(), status_observer=motion_status)
            motion_status(session.status(time.perf_counter()))
        def control(now: float) -> str:
            # Only fixed, short byte commands from the parent. Any invalid input aborts.
            if controls is not None and controls.poll():
                try:
                    command = controls.recv_bytes(16).decode("ascii")
                except (OSError, UnicodeError, EOFError):
                    command = "invalid"
                session.command(command, time.perf_counter())
            return session.poll(time.perf_counter())
        result = execute_probe(sdk, port=port, process_id=process_id,
            config=config, progress=progress,
            pose_observer=session.consume if session is not None else None,
            observation_control=control if session is not None else None)
        if session is not None:
            session.end_observation(time.perf_counter())
            motion_status(session.status(time.perf_counter()))
        progress({"stage": "result_ready", "elapsed_seconds": time.perf_counter() - started,
                  "aggregate": result})
    except BaseException:
        try:
            checkpoint("child_error")
        except BaseException:
            pass
    finally:
        connection.close()
        if controls is not None:
            controls.close()


def supervise_probe(*, sdk_root: Path, port: int, process_id: int,
                    config: ProbeConfig, hard_timeout_seconds: float = 45.0,
                    motion_cue: Optional[str] = None,
                    command_source: Optional[Callable[[], Optional[str]]] = None,
                    status_observer: Optional[Callable[[dict], None]] = None,
                    _sdk_loader: Callable[[str], Any] = _load_official_sdk) -> dict:
    """Spawn one child, retain latest aggregate, and bound every parent wait.

    Time includes process startup and cleanup; OS scheduling is not hard realtime.
    A reader daemon alone may block on a partial IPC frame, never the controller.
    The private loader seam is only for synthetic tests, not an alternate SDK API.
    """
    if not isinstance(config, ProbeConfig):
        raise ValueError("config must be ProbeConfig")
    if motion_cue is not None:
        from research.controlled_motion_session import CUES
        if motion_cue not in CUES or config.duration_seconds > 55 or command_source is None:
            raise ValueError("invalid controlled motion configuration")
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
    control_receive, control_send = context.Pipe(duplex=False) if motion_cue is not None else (None, None)
    child = context.Process(target=_child_probe, args=(
        send, str(sdk_root), port, process_id, asdict(config), _sdk_loader,
        motion_cue, control_receive), daemon=True)
    # Only the reader writes these references. No child-owned lock is acquired.
    latest: dict = {"packet": None, "aggregate": None, "count": 0, "invalid": 0,
                   "received_at": None, "motion": None}
    reader_done = threading.Event()

    def read_progress() -> None:
        try:
            while True:
                try:
                    packet = _clean_packet(json.loads(receive.recv_bytes(MAX_PACKET_BYTES)), template, motion_cue)
                except (ValueError, UnicodeError, json.JSONDecodeError):
                    latest["invalid"] += 1
                    continue
                latest["packet"] = packet
                latest["received_at"] = time.perf_counter()
                if "aggregate" in packet:
                    latest["aggregate"] = packet["aggregate"]
                if "motion" in packet:
                    latest["motion"] = packet["motion"]
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
    last_motion_state, commands_sent = None, 0
    command_queue: queue.Queue = queue.Queue(maxsize=16)
    control_error = threading.Event()
    def write_controls() -> None:
        try:
            while True:
                command = command_queue.get()
                if command is None:
                    return
                control_send.send_bytes(command)
        except (OSError, EOFError):
            control_error.set()
        finally:
            control_send.close()
    try:
        child.start()
        send.close()
        if control_receive is not None:
            control_receive.close()
            threading.Thread(target=write_controls, daemon=True).start()
        threading.Thread(target=read_progress, daemon=True).start()
        while child.is_alive() and time.perf_counter() < stop_at:
            if command_source is not None and control_send is not None and commands_sent < 16:
                command = command_source()
                if command is not None:
                    from research.controlled_motion_session import COMMANDS
                    fixed_command = command if command in COMMANDS else "invalid"
                    # A dedicated daemon owns writes; a stalled child never blocks parent IPC.
                    command_queue.put_nowait(fixed_command.encode("ascii"))
                    commands_sent += 1
            if control_error.is_set():
                raise RuntimeError("control channel unavailable")
            motion = latest["motion"]
            if motion is not None and motion["state"] != last_motion_state:
                last_motion_state = motion["state"]
                if status_observer is not None:
                    status_observer({key: value for key, value in motion.items() if key != "cue_result"})
            child.join(min(0.025, max(0.0, stop_at - time.perf_counter())))
        if child.is_alive():
            reason, termination_requested = "DEADLINE", True
            try:
                child.terminate()
            except (OSError, PermissionError):
                termination_error = True
            child.join(max(0.0, deadline - time.perf_counter() - 0.05))
        reader_done.wait(max(0.0, min(0.05, deadline - time.perf_counter())))
        if (latest["motion"] is not None and latest["motion"]["state"] != last_motion_state
                and status_observer is not None):
            status_observer({key: value for key, value in latest["motion"].items() if key != "cue_result"})
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
        if control_send is not None:
            try:
                command_queue.put_nowait(None)
            except queue.Full:
                pass
    ended = time.perf_counter()
    alive = child.is_alive() if child.pid is not None else False
    packet, aggregate = latest["packet"], latest["aggregate"]
    complete = packet is not None and packet["stage"] == "result_ready"
    clean_exit = (complete and isinstance(aggregate, dict) and not alive and child.exitcode == 0
                  and not termination_requested and not termination_error
                  and not latest["invalid"] and ended <= deadline
                  and reason == "CHILD_EXIT")
    status = aggregate.get("status", "UNVERIFIED") if clean_exit else "UNVERIFIED"
    if motion_cue is not None:
        motion = latest["motion"]
        if clean_exit and motion is not None and status not in ("ABORTED", "FAIL"):
            status = (motion["cue_result"]["result"] if motion["state"] == "COMPLETE"
                      and motion["cue_result"] is not None and status == "PASS"
                      else "ABORTED" if motion["state"] == "ABORTED"
                      else "INCOMPLETE" if motion["state"] == "INCOMPLETE" else "UNVERIFIED")
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
    if motion_cue is not None:
        report["motion"] = latest["motion"]
        report["control_commands_sent"] = commands_sent
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
    parser.add_argument("--motion-cue", choices=("right", "forward", "crouch", "left_knee",
        "right_knee", "yaw_left", "yaw_right", "left_arm", "right_arm", "left_shoulder", "right_shoulder"))
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
            process_id=args.process_id, config=config, hard_timeout_seconds=args.hard_timeout_seconds,
            motion_cue=args.motion_cue,
            command_source=stdin_command_source() if args.motion_cue is not None else None,
            status_observer=print_motion_status if args.motion_cue is not None else None)
    except (TypeError, ValueError):
        parser.error("invalid explicit probe configuration")
    if args.motion_cue is not None:
        # Public motion output retains relative duration, not process IDs or absolute clocks.
        report = {key: value for key, value in report.items() if key not in (
            "start_perf_counter", "deadline_perf_counter", "end_perf_counter", "child_pid")}
    print("RESULT_JSON=" + json.dumps(report, allow_nan=False, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


def print_motion_status(status: dict) -> None:
    print("STATUS_JSON=" + json.dumps(status, allow_nan=False, separators=(",", ":")), flush=True)


def stdin_command_source() -> Callable[[], Optional[str]]:
    """Read fixed line commands without allowing console reads to block watchdog."""
    from research.controlled_motion_session import COMMANDS
    pending: queue.Queue = queue.Queue(maxsize=8)
    def read_commands() -> None:
        while True:
            line = sys.stdin.readline(32)
            command = line.strip() if line else "stop"
            command = command if command in COMMANDS else "invalid"
            try:
                pending.put_nowait(command)
            except queue.Full:
                return
            if not line or command == "stop":
                return
    threading.Thread(target=read_commands, daemon=True).start()
    def next_command() -> Optional[str]:
        try:
            return pending.get_nowait()
        except queue.Empty:
            return None
    return next_command


if __name__ == "__main__":
    # Avoid multiprocessing's implicit unbounded atexit join if OS termination failed.
    os._exit(main())
