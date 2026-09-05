"""One scheduled countdown cue using the existing supervised SDK probe.

Speech completion is not evidence that the user heard or performed a motion.
The caller must establish the Safe Point and obtain readiness before launch.
Deadlines are software bounds, not hard real-time guarantees: OS process launch
and caller-supplied status callbacks must return promptly.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import signal
import sys
import time
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.controlled_motion_analysis import CUES
from research.live_retarget_safety_probe import ProbeConfig
from research.supervised_retarget_probe import (
    _load_official_sdk, supervise_probe, stdin_command_source, print_motion_status,
)

_MOVE_PHRASES = {
    "right": "体の向きを変えず、右へ少し移動します。", "forward": "体の向きを変えず、前へ少し移動します。",
    "crouch": "無理なく浅くしゃがみます。",
    "left_knee": "支えを使い左ひざを軽く曲げます。",
    "right_knee": "支えを使い右ひざを軽く曲げます。",
    "yaw_left": "楽な範囲で左を向きます。", "yaw_right": "楽な範囲で右を向きます。",
    "left_arm": "左腕を楽な範囲で上げます。", "right_arm": "右腕を楽な範囲で上げます。",
    "left_shoulder": "左肩を軽く前へ出します。", "right_shoulder": "右肩を軽く前へ出します。",
}


class LocalSpeech:
    """Exactly one hidden, local standard Windows speech subprocess."""
    def __init__(self, cue: str, stage: str):
        if sys.platform != "win32" or cue not in CUES or stage not in ("initial_neutral", "move", "return", "finish"):
            raise ValueError("local speech unavailable")
        phrase = {
            "initial_neutral": "元の位置で楽に立ち、体の向きを保って静止してください。",
            "move": _MOVE_PHRASES[cue],
            "return": ("体の向きを変えず、元の位置へ戻ります。" if cue in ("right", "forward")
                       else "元の位置と楽な姿勢へ戻ります。"),
            "finish": "計測は終了です。楽にしてください。",
        }[stage]
        countdown = (
            "foreach($n in @(3,2,1)){$s.Speak([string]$n);Start-Sleep -Milliseconds 700};"
            "$s.Speak('どうぞ。その位置と姿勢で静止してください。');"
            if stage in ("move", "return") else ""
        )
        # Every interpolated word comes from the fixed phrases above, never user text.
        script = (
            "$ErrorActionPreference='Stop'; try {"
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$voices=@($s.GetInstalledVoices() | Where-Object {$_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'ja-JP'});"
            "if($voices.Count -eq 0){exit 2}; $s.SelectVoice($voices[0].VoiceInfo.Name);"
            "$s.SetOutputToDefaultAudioDevice();"
            f"$s.Speak('{phrase}');"
            f"{countdown}$s.Dispose();exit 0"
            "}catch{exit 3}"
        )
        self.process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def poll(self):
        return self.process.poll()

    def cancel(self):
        if self.process.poll() is None:
            self.process.terminate()

    def close(self, timeout: float) -> bool:
        self.cancel()
        try:
            self.process.wait(timeout=max(0., timeout))
        except subprocess.TimeoutExpired:
            return False
        return True


class CountdownCue:
    """Nonblocking state-aware commands; no thread, sleep, SDK, or socket."""
    def __init__(self, cue: str, *, speech_factory: Callable = LocalSpeech,
                 clock: Callable[[], float] = time.perf_counter,
                 stop_source: Callable[[], Optional[str]] = lambda: None):
        if cue not in CUES:
            raise ValueError("unknown cue")
        self.cue, self.clock, self.started = cue, clock, clock()
        if type(self.started) not in (int, float) or not math.isfinite(self.started):
            raise ValueError("invalid countdown clock")
        self._last_time = self.started
        self.speech_factory, self.stop_source = speech_factory, stop_source
        self.state, self.phase, self.error = None, "WAIT_BASELINE", "NONE"
        self.job = None
        self.job_started = self.settle_until = None
        self.speech_started = self.speech_completed = 0
        self.completed_speech_stages = []
        self.commands_sent = 0
        self._stop_sent = False

    def on_status(self, status: dict) -> None:
        from research.controlled_motion_session import STATES
        state = status.get("state")
        if status.get("cue") != self.cue or state not in STATES:
            self._fail("STATUS_MISMATCH")
            return
        self.state = state
        if state in ("COMPLETE", "INCOMPLETE", "ABORTED"):
            self.phase = "FINISHED"
            self._cancel()

    def _cancel(self):
        if self.job is not None:
            try:
                self.job.cancel()
            except Exception:
                self.error = "SPEECH_CLEANUP_FAILED"

    def _fail(self, reason):
        self.error, self.phase = reason, "FAILED"
        self._cancel()

    def _command(self, command, phase):
        self.phase = phase
        self.commands_sent += 1
        return command

    def start_speech(self, stage: str, now: float) -> None:
        try:
            if self.job is not None and not self.job.close(0):
                self._fail("SPEECH_CLEANUP_FAILED")
                return
            self.job = self.speech_factory(self.cue, stage)
            self.speech_started += 1
            self.job_started, self.speech_stage = now, stage
        except Exception:
            self._fail("SPEECH_START_FAILED")

    def speech_done(self, now: float) -> bool:
        # A late successful poll is still too late; never manufacture a boundary.
        if now - self.job_started >= 12:
            self._fail("SPEECH_TIMEOUT")
            return False
        try:
            result = self.job.poll()
        except Exception:
            result = -1
        if result is None:
            return False
        if result != 0:
            self._fail("SPEECH_FAILED")
            return False
        self.speech_completed += 1
        self.completed_speech_stages.append(self.speech_stage)
        return True

    def __call__(self) -> Optional[str]:
        now = self.clock()
        if type(now) not in (int, float) or not math.isfinite(now) or now < self._last_time:
            self._fail("CLOCK_ORDER")
        else:
            self._last_time = now
        if self.phase != "FINISHED" and self.stop_source() is not None:
            self._fail("USER_STOP")
        if self.error != "NONE":
            if not self._stop_sent:
                self._stop_sent = True
                return "stop"
            return None
        if self.phase == "FINISHED":
            return None
        if now - self.started >= 54:
            self._fail("COUNTDOWN_DEADLINE")
            return self()
        if self.phase == "WAIT_BASELINE" and self.state == "WAIT_BASELINE":
            self.start_speech("initial_neutral", now)
            if self.error != "NONE":
                return self()
            self.phase = "INITIAL_SPEECH"
        if self.phase == "INITIAL_SETTLE" and now >= self.settle_until:
            return self._command("baseline", "WAIT_READY_MOVE")
        if self.phase == "WAIT_READY_MOVE" and self.state == "READY_MOVE":
            if now - self.started >= 45:
                self._fail("CUE_CUTOFF")
                return self()
            # Wait for child acknowledgment before beginning any motion instruction.
            return self._command("move", "WAIT_MOVE_ACCEPTED")
        if self.phase == "WAIT_READY_RETURN" and self.state == "READY_RETURN":
            return self._command("return", "WAIT_RETURN_ACCEPTED")
        if ((self.phase == "WAIT_MOVE_ACCEPTED" and self.state == "WAIT_HOLD")
                or (self.phase == "WAIT_RETURN_ACCEPTED" and self.state == "WAIT_NEUTRAL")):
            returning = self.phase == "WAIT_RETURN_ACCEPTED"
            self.start_speech("return" if returning else "move", now)
            if self.error != "NONE":
                return self()
            self.phase = "RETURN_SPEECH" if returning else "MOVE_SPEECH"
        if self.phase in ("INITIAL_SPEECH", "MOVE_SPEECH", "RETURN_SPEECH"):
            done = self.speech_done(now)
            if self.error != "NONE":
                return self()
            if done:
                self.settle_until = now + 4
                self.phase = self.phase.replace("SPEECH", "SETTLE")
        if self.phase == "MOVE_SETTLE" and now >= self.settle_until:
            return self._command("hold", "WAIT_READY_RETURN")
        if self.phase == "RETURN_SETTLE" and now >= self.settle_until:
            return self._command("neutral", "WAIT_COMPLETE")
        return None

    def close(self, timeout: float) -> bool:
        self.phase = "FINISHED"
        if self.job is None:
            return True
        try:
            clean = self.job.close(timeout)
        except Exception:
            clean = False
        if not clean:
            self.error = "SPEECH_CLEANUP_FAILED"
        return clean

    def evidence(self) -> dict:
        return {"marker_source": "SCHEDULED_COUNTDOWN", "user_confirmation": "PENDING",
                "speech_started": self.speech_started, "speech_completed": self.speech_completed,
                "completed_speech_stages": list(self.completed_speech_stages),
                "commands_sent": self.commands_sent, "error": self.error,
                "speech_audibility": "UNVERIFIED"}


def run_countdown(*, sdk_root: Path, port: int, process_id: int, cue: str,
                  user_ready: bool, stop_source: Callable = lambda: None,
                  status_observer: Optional[Callable] = None,
                  _sdk_loader: Callable = _load_official_sdk,
                  _speech_factory: Callable = LocalSpeech) -> dict:
    if user_ready is not True:
        raise ValueError("explicit user readiness is required")
    started = time.perf_counter()
    controller = CountdownCue(cue, speech_factory=_speech_factory, stop_source=stop_source)
    def status(value):
        controller.on_status(value)
        if status_observer is not None:
            status_observer(value)
    try:
        remaining = started + 59.5 - time.perf_counter()
        if remaining < 56:
            raise ValueError("insufficient supervised observation budget")
        report = supervise_probe(sdk_root=sdk_root, port=port, process_id=process_id,
            config=ProbeConfig(duration_seconds=55, consumer_hz=60), hard_timeout_seconds=remaining,
            motion_cue=cue, command_source=controller, status_observer=status,
            _sdk_loader=_sdk_loader)
        aggregate = report.get("aggregate") or {}
        life = aggregate.get("lifecycle", {})
        # Completion speech describes the ended capture, never semantic PASS.
        # It starts only after the SDK child has exited normally, inside the
        # original overall deadline; failures do not launch another body cue.
        if (controller.error == "NONE" and controller.state == "COMPLETE"
                and (report.get("motion") or {}).get("state") == "COMPLETE"
                and aggregate.get("abort_reason") == "NONE"
                and life.get("sdk_close_successes") == 1
                and report.get("status") != "ABORTED"
                and report.get("child_exit_observed") is True and report.get("child_exit_code") == 0
                and report.get("result_ready") is True and report.get("supervisor_reason") == "CHILD_EXIT"
                and report.get("within_deadline") is True and not report.get("termination_requested")
                and not report.get("termination_error") and report.get("invalid_packet_count") == 0):
            if stop_source() is not None:
                controller._fail("USER_STOP")
            elif time.perf_counter() >= started + 59.5:
                controller._fail("COUNTDOWN_DEADLINE")
            else:
                controller.start_speech("finish", time.perf_counter())
                while controller.error == "NONE":
                    now = time.perf_counter()
                    if stop_source() is not None:
                        controller._fail("USER_STOP")
                    elif now >= started + 59.5:
                        controller._fail("COUNTDOWN_DEADLINE")
                    elif controller.speech_done(now):
                        break
                    else:
                        time.sleep(min(.01, max(0., started + 59.5 - now)))
    finally:
        audio_exit = controller.close(max(0., min(.4, started + 60 - time.perf_counter())))
    elapsed = time.perf_counter() - started
    report = dict(report)
    report["numerical_status"] = report["status"]
    report["countdown"] = controller.evidence()
    report["countdown"]["audio_exit_observed"] = audio_exit
    report["total_elapsed_seconds_including_audio_cleanup"] = elapsed
    aggregate = report.get("aggregate") or {}
    life, counts = aggregate.get("lifecycle", {}), aggregate.get("counts", {})
    # A scheduled timeout with no input is an absence of evidence, not evidence
    # of bad motion. Do not reclassify explicit stops, SDK faults or forced exit.
    empty_clean_timeout = (
        controller.error == "COUNTDOWN_DEADLINE"
        and (controller.speech_started == 0 or (
            controller.speech_started == controller.speech_completed == 1
            and controller.completed_speech_stages == ["initial_neutral"]))
        and counts.get("callbacks_received") == 0
        and aggregate.get("abort_reason") == "USER_STOP"
        and life.get("sdk_open_successes") == 1 and life.get("sdk_close_successes") == 1
        and report.get("child_exit_observed") is True and report.get("child_exit_code") == 0
        and report.get("result_ready") is True and report.get("supervisor_reason") == "CHILD_EXIT"
        and report.get("within_deadline") is True and not report.get("termination_requested")
        and not report.get("termination_error") and report.get("invalid_packet_count") == 0
        and audio_exit and elapsed <= 60
    )
    if empty_clean_timeout:
        report["status"] = "UNVERIFIED"
    elif controller.error != "NONE" or not audio_exit or elapsed > 60:
        report["status"] = "ABORTED"
    elif report["status"] == "PASS":
        report["status"] = "UNVERIFIED"
    # Scheduled sample boundaries are not human acknowledgments or physical proof.
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--process-id", type=int, required=True)
    parser.add_argument("--motion-cue", choices=CUES, required=True)
    parser.add_argument("--user-ready", action="store_true", required=True)
    args = parser.parse_args(argv)
    def cancel(_signal, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, cancel)
    signal.signal(signal.SIGTERM, cancel)
    try:
        report = run_countdown(sdk_root=args.sdk_root, port=args.port, process_id=args.process_id,
            cue=args.motion_cue, user_ready=args.user_ready, stop_source=stdin_command_source(),
            status_observer=print_motion_status)
    except (TypeError, ValueError):
        parser.error("invalid explicit countdown configuration")
    public = {key: value for key, value in report.items() if key not in (
        "start_perf_counter", "deadline_perf_counter", "end_perf_counter", "child_pid")}
    print("RESULT_JSON="+json.dumps(public, allow_nan=False), flush=True)
    return 0 if report["status"] != "ABORTED" else 1


if __name__ == "__main__":
    os._exit(main())
