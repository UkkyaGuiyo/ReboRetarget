"""One user-marked motion, bounded RAM windows, no SDK or output transport."""
from __future__ import annotations

import math
from typing import Callable, Optional

from research.controlled_motion_analysis import CUES, MotionFrame, analyze_cue, clean_cue_result

COMMANDS = frozenset(("baseline", "move", "hold", "return", "neutral", "stop"))
STATES = frozenset(("WAIT_BASELINE", "BASELINE", "READY_MOVE", "WAIT_HOLD", "HOLD",
                    "READY_RETURN", "WAIT_NEUTRAL", "RETURN", "COMPLETE", "INCOMPLETE", "ABORTED"))
REASONS = frozenset(("NONE", "USER_STOP", "INVALID_COMMAND", "MARKER_TIMEOUT",
                     "CUE_CUTOFF", "OBSERVATION_ENDED", "CLOCK_ORDER", "SEQUENCE_ORDER"))
_EXPECTED = {"WAIT_BASELINE": "baseline", "READY_MOVE": "move", "WAIT_HOLD": "hold",
             "READY_RETURN": "return", "WAIT_NEUTRAL": "neutral"}


def clean_session_status(value: dict, cue: str) -> dict:
    keys = {"schema", "cue", "state", "reason", "counts", "elapsed_seconds", "cue_result"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "reboretarget.phase2f-a.session.v1"
            or cue not in CUES or value["cue"] != cue
            or value["state"] not in STATES or value["reason"] not in REASONS):
        raise ValueError("invalid session status")
    counts = value["counts"]
    if not isinstance(counts, dict) or set(counts) != {"baseline", "held", "returned"}:
        raise ValueError("invalid session counts")
    if any(type(counts[name]) is not int or not 0 <= counts[name] <= limit
           for name, limit in (("baseline", 60), ("held", 20), ("returned", 20))):
        raise ValueError("invalid session counts")
    elapsed = value["elapsed_seconds"]
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed < 3600:
        raise ValueError("invalid session duration")
    result = dict(value, counts=dict(counts))
    if result["cue_result"] is not None:
        result["cue_result"] = clean_cue_result(result["cue_result"])
        if result["cue_result"]["cue"] != cue:
            raise ValueError("cue mismatch")
    return result


class ControlledMotionSession:
    """Fixed 60/20/20 samples after markers; at most 100 raw frames in RAM.

    Marker time and sample receive time share the injected perf-counter domain.
    Never cues the user's body itself: commands represent explicit user markers.
    """
    def __init__(self, cue: str, source_bind, *, started: float,
                 status_observer: Optional[Callable[[dict], None]] = None):
        if cue not in CUES or not math.isfinite(started) or started < 0:
            raise ValueError("invalid controlled session")
        self.cue, self.source_bind, self.started = cue, source_bind, started
        self.state, self.reason = "WAIT_BASELINE", "NONE"
        self._state_since = self._last_time = started
        self._marker, self._last_sequence = started, 0
        self._windows = {"baseline": [], "held": [], "returned": []}
        self.counts = {"baseline": 0, "held": 0, "returned": 0}
        self.cue_result = None
        self._status_observer = status_observer

    @property
    def finished(self) -> bool:
        return self.state in ("COMPLETE", "INCOMPLETE", "ABORTED")

    def _transition(self, state: str, now: float, reason: str = "NONE") -> None:
        self.state, self.reason, self._state_since = state, reason, now
        if self.finished:
            for window in self._windows.values():
                window.clear()
        if self._status_observer is not None:
            self._status_observer(self.status(now))

    def command(self, command: str, now: float) -> None:
        if self.finished:
            return
        if not math.isfinite(now) or now < self._last_time:
            self._transition("ABORTED", self._last_time, "CLOCK_ORDER")
            return
        self._last_time = now
        if command == "stop":
            self._transition("ABORTED", now, "USER_STOP")
            return
        if command not in COMMANDS or _EXPECTED.get(self.state) != command:
            self._transition("ABORTED", now, "INVALID_COMMAND")
            return
        if now - self._state_since >= 20:
            self._transition("INCOMPLETE", now, "MARKER_TIMEOUT")
            return
        if command == "move" and now - self.started >= 45:
            self._transition("INCOMPLETE", now, "CUE_CUTOFF")
            return
        self._marker = now
        self._transition({"baseline": "BASELINE", "move": "WAIT_HOLD", "hold": "HOLD",
                          "return": "WAIT_NEUTRAL", "neutral": "RETURN"}[command], now)

    def poll(self, now: float) -> str:
        if not math.isfinite(now) or now < self._last_time:
            self._transition("ABORTED", self._last_time, "CLOCK_ORDER")
        else:
            self._last_time = now
            if not self.finished and self.state in _EXPECTED and now - self._state_since >= 20:
                self._transition("INCOMPLETE", now, "MARKER_TIMEOUT")
            elif self.state == "READY_MOVE" and now - self.started >= 45:
                self._transition("INCOMPLETE", now, "CUE_CUTOFF")
        return "ABORT" if self.state == "ABORTED" else "COMPLETE" if self.finished else "CONTINUE"

    def consume(self, sequence: int, receive: float, delta, canonical, anchors) -> None:
        if self.finished:
            return
        if sequence <= self._last_sequence or not math.isfinite(receive):
            self._transition("ABORTED", self._last_time, "SEQUENCE_ORDER")
            return
        self._last_sequence = sequence
        if receive < self._marker:
            return
        selected = {"BASELINE": ("baseline", 60, "READY_MOVE"),
                    "HOLD": ("held", 20, "READY_RETURN"),
                    "RETURN": ("returned", 20, "COMPLETE")}.get(self.state)
        if selected is None:
            return
        name, maximum, following = selected
        self._windows[name].append(MotionFrame(delta, canonical, tuple(anchors)))
        self.counts[name] += 1
        if self.counts[name] == maximum:
            if following == "COMPLETE":
                self.cue_result = analyze_cue(self.cue, self._windows["baseline"],
                    self._windows["held"], self._windows["returned"], self.source_bind)
            self._transition(following, max(receive, self._last_time))

    def end_observation(self, now: float) -> None:
        if not self.finished:
            self._transition("INCOMPLETE", max(now, self._last_time), "OBSERVATION_ENDED")

    def status(self, now: float) -> dict:
        return {"schema": "reboretarget.phase2f-a.session.v1", "cue": self.cue,
                "state": self.state, "reason": self.reason, "counts": dict(self.counts),
                "elapsed_seconds": max(0.0, now - self.started), "cue_result": self.cue_result}
