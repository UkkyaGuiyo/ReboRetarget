"""Atomic capacity-one state for already-validated pose values.

The caller supplies all timestamps and lifecycle events.  Payloads are neither
validated nor copied; ``None`` may itself be an opaque valid value.  A Pose
caller must publish an already-validated immutable value and not mutate it
afterward.  This module owns no clock, worker thread, timer, scheduler, queue,
reconnect behavior, or I/O.  One ``threading.Lock`` makes each multi-field
state transition atomic between a future SDK callback and consumer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import threading
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class LatestPoseState(Enum):
    EMPTY = "empty"
    VALID = "valid"
    STALE = "stale"
    DISCONNECTED = "disconnected"


class PublishResult(Enum):
    ACCEPTED = "accepted"
    REJECTED_INACTIVE = "rejected_inactive"
    REJECTED_RECEIVE_ORDER = "rejected_receive_order"
    REJECTED_SOURCE_ORDER = "rejected_source_order"


@dataclass(frozen=True, slots=True)
class LatestPoseSample(Generic[T]):
    sequence: int
    value: T
    receive_monotonic: float
    source_timestamp: float


@dataclass(frozen=True, slots=True)
class LatestPoseSnapshot(Generic[T]):
    state: LatestPoseState
    sample: Optional[LatestPoseSample[T]]


def _finite_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite and not Boolean")
    try:
        converted = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite") from error
    if not math.isfinite(converted):
        raise ValueError(f"{label} must be finite")
    return converted


def _finite_nonnegative(value: float, label: str) -> float:
    converted = _finite_float(value, label)
    if converted < 0.0:
        raise ValueError(f"{label} must be non-negative")
    return converted


class LatestPoseSlot(Generic[T]):
    """Hold at most one current value and preserve ordering watermarks."""

    __slots__ = (
        "_stale_after_seconds",
        "_lock",
        "_state",
        "_sample",
        "_sequence",
        "_last_receive_monotonic",
        "_last_source_timestamp",
    )

    def __init__(self, stale_after_seconds: float) -> None:
        stale_after = _finite_float(stale_after_seconds, "stale_after_seconds")
        if stale_after <= 0.0:
            raise ValueError("stale_after_seconds must be positive")
        self._stale_after_seconds = stale_after
        self._lock = threading.Lock()
        self._state = LatestPoseState.EMPTY
        self._sample: Optional[LatestPoseSample[T]] = None
        self._sequence = 0
        self._last_receive_monotonic: Optional[float] = None
        self._last_source_timestamp: Optional[float] = None

    @property
    def stale_after_seconds(self) -> float:
        return self._stale_after_seconds

    def publish(
        self,
        value: T,
        *,
        receive_monotonic: float,
        source_timestamp: float,
    ) -> PublishResult:
        """Atomically replace the sole sample when both timestamps advance."""

        receive = _finite_nonnegative(receive_monotonic, "receive_monotonic")
        source = _finite_float(source_timestamp, "source_timestamp")
        with self._lock:
            if self._state not in (LatestPoseState.EMPTY, LatestPoseState.VALID):
                return PublishResult.REJECTED_INACTIVE
            if (
                self._last_receive_monotonic is not None
                and receive <= self._last_receive_monotonic
            ):
                return PublishResult.REJECTED_RECEIVE_ORDER
            if (
                self._last_source_timestamp is not None
                and source <= self._last_source_timestamp
            ):
                return PublishResult.REJECTED_SOURCE_ORDER

            self._sequence += 1
            self._sample = LatestPoseSample(
                sequence=self._sequence,
                value=value,
                receive_monotonic=receive,
                source_timestamp=source,
            )
            self._last_receive_monotonic = receive
            self._last_source_timestamp = source
            self._state = LatestPoseState.VALID
            return PublishResult.ACCEPTED

    def snapshot_at(self, now_monotonic: float) -> LatestPoseSnapshot[T]:
        """Return one atomic snapshot, invalidating values older than the limit."""

        now = _finite_nonnegative(now_monotonic, "now_monotonic")
        with self._lock:
            if self._state is LatestPoseState.VALID:
                sample = self._sample
                if sample is None:
                    raise RuntimeError("VALID state must contain a sample")
                age = now - sample.receive_monotonic
                if age > self._stale_after_seconds:
                    self._state = LatestPoseState.STALE
                    self._sample = None
            return LatestPoseSnapshot(self._state, self._sample)

    def mark_stale(self) -> None:
        """Invalidate the current value unless disconnection already dominates."""

        with self._lock:
            if self._state is not LatestPoseState.DISCONNECTED:
                self._state = LatestPoseState.STALE
                self._sample = None

    def mark_disconnected(self) -> None:
        """Invalidate the current value and enter the dominant inactive state."""

        with self._lock:
            self._state = LatestPoseState.DISCONNECTED
            self._sample = None

    def rearm(self) -> None:
        """Return an inactive slot to EMPTY without reconnecting or resetting order."""

        with self._lock:
            if self._state is LatestPoseState.VALID:
                raise RuntimeError("cannot rearm a VALID latest-pose slot")
            if self._state in (LatestPoseState.STALE, LatestPoseState.DISCONNECTED):
                self._state = LatestPoseState.EMPTY
                self._sample = None
