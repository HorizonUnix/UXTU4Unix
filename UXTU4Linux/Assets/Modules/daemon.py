"""
daemon.py
"""
from __future__ import annotations

import json
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
import zmq
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.realpath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
ZMQ_POLL_TIMEOUT_MS = 500
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Assets.Modules import config as cfg

cfg.load()

# Traditional AC/mains power-supply types.
_AC_TYPES = frozenset({"Mains"})
# USB-derived power supplies are treated as external power for policy decisions.
_USB_POWER_TYPES = frozenset({"USB", "USB_C", "USB_PD", "USB_PD_DRP", "USB_C_DRP"})
_EXTERNAL_POWER_TYPES = _AC_TYPES | _USB_POWER_TYPES

_DMI_ALLOWED_TYPES = frozenset({
    "bios", "system", "baseboard", "chassis", "processor",
    "memory", "cache", "connector", "slot",
    *(str(i) for i in range(42)),
})

MIN_INTERVAL_SECONDS: int = 1
MAX_INTERVAL_SECONDS: int = 3600
COMMAND_TIMEOUT_SECONDS: int = 10

_RYZENADJ_TOKEN_RE = re.compile(
    r'^--?[a-zA-Z][a-zA-Z0-9_-]*(=\S+)?$'
)

def _validate_ryzenadj_payload(tokens: list[str]) -> list[str]:
    invalid = [t for t in tokens if not _RYZENADJ_TOKEN_RE.match(t)]
    if invalid:
        raise ValueError(f"invalid ryzenadj arguments: {invalid}")
    return tokens


def _run_cmd(command: str) -> str:
    try:
        args = shlex.split(command)
    except ValueError as exc:
        logging.warning("Failed to parse command %r: %s", command, exc)
        return ""
    try:
        proc = subprocess.Popen(
            args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        logging.warning("Failed to start command %r: %s", command, exc)
        return ""
    try:
        stdout, _ = proc.communicate(timeout=COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        logging.warning("Command timed out after %ss: %r", COMMAND_TIMEOUT_SECONDS, command)
        return ""
    if proc.returncode != 0:
        logging.debug("Command exited with non-zero status %s: %r", proc.returncode, command)
    return stdout.decode("utf-8", errors="replace").strip()


def _on_ac() -> bool:
    ac_online = False
    found_ac = False
    battery_discharging = False
    try:
        for entry in os.listdir("/sys/class/power_supply"):
            base = f"/sys/class/power_supply/{entry}"
            try:
                with open(f"{base}/type") as f:
                    ptype = f.read().strip()
            except OSError:
                continue
            if ptype in _EXTERNAL_POWER_TYPES:
                found_ac = True
                try:
                    with open(f"{base}/online") as f:
                        if f.read().strip() == "1":
                            ac_online = True
                except OSError as exc:
                    logging.debug("Failed to read AC online state from %s/online: %s", base, exc)
            elif ptype == "Battery":
                try:
                    with open(f"{base}/status") as f:
                        if f.read().strip().lower() == "discharging":
                            battery_discharging = True
                except OSError as exc:
                    logging.debug("Unable to read battery status from %s/status: %s", base, exc)
    except Exception as exc:
        logging.debug("Unexpected error while detecting AC state: %s", exc)
    if found_ac:
        return ac_online
    return not battery_discharging


def _load_presets() -> dict:
    from Assets.Modules.power import get_presets
    return get_presets()


def _run_ryzenadj(args: str, mode: str) -> str:
    raw_payload = mode.split() if args == "Custom" else args.split()
    try:
        payload = _validate_ryzenadj_payload(raw_payload)
    except ValueError as exc:
        logging.error("%s", exc)
        return ""

    try:
        result = subprocess.run(
            [cfg.RYZENADJ] + payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logging.error("ryzenadj timed out")
        return ""

    out = result.stdout.decode(errors="replace")
    if cfg.is_debug() and result.stderr:
        out += result.stderr.decode(errors="replace")
    return out.strip()


def _parse_interval(raw_interval: int | str | None, default: int) -> int:
    try:
        value = int(raw_interval)
    except (TypeError, ValueError):
        value = default
    return max(MIN_INTERVAL_SECONDS, min(MAX_INTERVAL_SECONDS, value))


@dataclass
class PresetState:
    mode:     str
    args:     str
    dynamic:  bool
    interval: int
    reapply:  bool


def _load_saved_preset() -> PresetState | None:
    cfg.load()
    user_mode = cfg.get("User", "Mode")
    presets   = _load_presets()

    if user_mode == "Custom":
        custom_args = cfg.get("User", "CustomArgs")
        if not isinstance(custom_args, str) or not custom_args.strip():
            logging.warning("Saved custom preset has no valid CustomArgs.")
            return None
        args = custom_args.strip()
    elif user_mode in presets:
        args = presets[user_mode]
    else:
        logging.warning("Saved preset %r not found.", user_mode)
        return None

    reapply  = cfg.get("Settings", "ReApply",     "0") == "1"
    dynamic  = cfg.get("Settings", "DynamicMode", "0") == "1"
    cfg_default = _parse_interval(cfg.get("Settings", "Time", "3"), 3)
    interval = cfg_default

    return PresetState(
        mode=user_mode,
        args=args,
        dynamic=dynamic,
        interval=interval,
        reapply=reapply,
    )


class PowerDaemon:
    def __init__(self) -> None:
        self._lock             = threading.Lock()
        self._loop_thread: threading.Thread | None = None
        self._stop_evt         = threading.Event()
        self._mode             = ""
        self._args             = ""
        self._dynamic          = False
        self._interval         = 3
        self._last_output      = ""
        self._running_loop     = False
        self._last_logged_mode = ""

        self._dispatch = {
            "ping":        self._cmd_ping,
            "apply":       self._cmd_apply,
            "apply_loop":  self._cmd_apply_loop,
            "stop_loop":   self._cmd_stop_loop,
            "status":      self._cmd_status,
            "apply_saved": self._cmd_apply_saved,
            "shutdown":    self._cmd_shutdown,
            "dmidecode":   self._cmd_dmidecode,
        }

    def _effective_mode_args(
        self, base_mode: str, base_args: str, dynamic: bool
    ) -> tuple[str, str]:
        if not dynamic:
            return base_mode, base_args
        presets = _load_presets()
        mode    = "Extreme" if _on_ac() else "Eco"
        args    = presets.get(mode, base_args)
        return mode, args

    def _apply_once(self, args: str, mode: str, *, log: bool = False) -> str:
        output = _run_ryzenadj(args, mode)
        with self._lock:
            self._mode        = mode
            self._args        = args
            self._last_output = output
        if log:
            logging.info("Applying preset: %s", mode)
        return output

    def _loop_body(self, args: str, mode: str, interval: int, dynamic: bool) -> None:
        if self._stop_evt.is_set():
            with self._lock:
                self._running_loop = False
            return
        max_wait_step = 1.0
        while not self._stop_evt.is_set():
            deadline = time.monotonic() + interval
            while not self._stop_evt.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._stop_evt.wait(min(remaining, max_wait_step))
            if self._stop_evt.is_set():
                break
            try:
                eff_mode, eff_args = self._effective_mode_args(mode, args, dynamic)
                changed = eff_mode != self._last_logged_mode
                self._apply_once(eff_args, eff_mode, log=changed)
                if changed:
                    self._last_logged_mode = eff_mode
            except Exception as exc:
                logging.warning("Failed to apply preset in loop: %s", exc)
        with self._lock:
            self._running_loop = False

    def _stop_loop(self) -> None:
        self._stop_evt.set()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=10)
            if self._loop_thread.is_alive():
                logging.warning("Loop thread did not terminate within 10 seconds")

    def apply_preset_state_once(self, state: PresetState) -> str:
        return self._apply_once(state.args, state.mode, log=True)

    def start_auto_reapply(self, state: PresetState) -> dict:
        return self._cmd_apply_loop({
            "args":     state.args,
            "mode":     state.mode,
            "interval": state.interval,
            "dynamic":  state.dynamic,
        })

    def _cmd_ping(self, _msg: dict) -> dict:
        return {"ok": True, "version": cfg.LOCAL_VERSION}

    def _cmd_apply(self, msg: dict) -> dict:
        try:
            mode   = msg.get("mode", "Unknown")
            args   = msg.get("args", "")
            output = self._apply_once(args, mode, log=True)
            self._last_logged_mode = mode
            return {"ok": True, "output": output}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _cmd_apply_loop(self, msg: dict) -> dict:
        args = msg.get("args", "")
        mode = msg.get("mode", "Unknown")

        cfg_default = _parse_interval(cfg.get("Settings", "Time", "3"), 3)
        interval    = _parse_interval(msg.get("interval", cfg_default), cfg_default)

        dynamic = bool(msg.get("dynamic", False))

        self._stop_loop()

        with self._lock:
            self._dynamic      = dynamic
            self._interval     = interval
            self._running_loop = True

        try:
            eff_mode, eff_args = self._effective_mode_args(mode, args, dynamic)
            self._apply_once(eff_args, eff_mode, log=True)
            self._last_logged_mode = eff_mode
        except Exception as exc:
            with self._lock:
                self._running_loop = False
            return {"ok": False, "error": str(exc)}

        logging.info(
            "Auto-reapply: every %ds%s",
            interval, ", dynamic" if dynamic else "",
        )

        self._loop_thread = threading.Thread(
            target=self._loop_body,
            args=(args, mode, interval, dynamic),
            daemon=True,
            name="uxtu-reapply",
        )
        self._loop_thread.start()
        return {"ok": True}

    def _cmd_stop_loop(self, _msg: dict) -> dict:
        self._stop_loop()
        with self._lock:
            self._running_loop = False
        logging.info("Auto-reapply stopped.")
        return {"ok": True}

    def _cmd_status(self, _msg: dict) -> dict:
        with self._lock:
            return {
                "ok":           True,
                "running_loop": self._running_loop,
                "mode":         self._mode,
                "args":         self._args,
                "dynamic":      self._dynamic,
                "interval":     self._interval,
                "on_ac":        _on_ac(),
                "last_output":  self._last_output,
            }

    def _cmd_apply_saved(self, _msg: dict) -> dict:
        try:
            state = _load_saved_preset()
        except Exception as exc:
            return {"ok": False, "error": f"Could not load presets: {exc}"}
        if state is None:
            return {"ok": False, "error": "Saved preset not found"}

        self._stop_loop()

        if state.reapply or state.dynamic:
            return self.start_auto_reapply(state)

        output = self.apply_preset_state_once(state)
        return {"ok": True, "output": output}

    def _cmd_shutdown(self, _msg: dict) -> dict:
        self._stop_loop()
        return {"ok": True}

    def _cmd_dmidecode(self, msg: dict) -> dict:
        dmi_type = msg.get("type", "")
        if not dmi_type:
            return {"ok": False, "error": "missing 'type'"}
        if dmi_type not in _DMI_ALLOWED_TYPES:
            return {"ok": False, "error": f"disallowed dmidecode type: {dmi_type!r}"}
        try:
            out = _run_cmd(f"{cfg.DMIDECODE} -t {dmi_type}")
            return {"ok": True, "output": out}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def handle(self, raw: str) -> str:
        try:
            msg  = json.loads(raw)
            cmd  = msg.get("cmd", "")
            func = self._dispatch.get(cmd)
            if func:
                resp = func(msg)
            else:
                resp = {"ok": False, "error": f"unknown command: {cmd!r}"}
        except Exception as exc:
            resp = {"ok": False, "error": str(exc)}
        return json.dumps(resp)

    @staticmethod
    def _sig_handler(stop_requested: threading.Event, *_: object) -> None:
        stop_requested.set()

    def run(self) -> None:
        if os.path.exists(cfg.ZMQ_SOCKET_PATH):
            try:
                os.unlink(cfg.ZMQ_SOCKET_PATH)
                logging.warning("Removed stale IPC socket at %s", cfg.ZMQ_SOCKET_PATH)
            except OSError as exc:
                logging.error("Could not remove stale socket at %s: %s", cfg.ZMQ_SOCKET_PATH, exc)

        ctx  = zmq.Context()
        sock = ctx.socket(zmq.REP)
        try:
            sock.bind(cfg.ZMQ_SOCKET_ADDR)
        except zmq.ZMQError as exc:
            logging.error("Failed to bind ZMQ socket on %s: %s", cfg.ZMQ_SOCKET_ADDR, exc)
            sock.close()
            ctx.term()
            return

        if os.path.exists(cfg.ZMQ_SOCKET_PATH):
            os.chmod(cfg.ZMQ_SOCKET_PATH, 0o660)

        logging.info("Listening on %s", cfg.ZMQ_SOCKET_ADDR)

        stop_requested = threading.Event()
        # Poll every 500ms so shutdown signals are handled within at most ~0.5s
        # while avoiding a tight loop that would wake the CPU too frequently.
        poll_timeout_ms = ZMQ_POLL_TIMEOUT_MS

        signal.signal(signal.SIGTERM, lambda *args: self._sig_handler(stop_requested, *args))
        signal.signal(signal.SIGINT,  lambda *args: self._sig_handler(stop_requested, *args))

        while True:
            if stop_requested.is_set():
                logging.info("Shutting down.")
                self._stop_loop()
                break

            if not sock.poll(poll_timeout_ms):
                continue

            raw  = sock.recv_string()
            resp = self.handle(raw)
            is_shutdown = False
            try:
                payload = json.loads(resp)
                if isinstance(payload, dict):
                    is_shutdown = bool(payload.get("shutdown", False))
            except (TypeError, ValueError):
                is_shutdown = False
            sock.send_string(resp)
            if is_shutdown:
                logging.info("Shutdown command received.")
                break

        if os.path.exists(cfg.ZMQ_SOCKET_PATH):
            os.unlink(cfg.ZMQ_SOCKET_PATH)
        sock.close()
        ctx.term()


def _apply_on_start(daemon: PowerDaemon) -> None:
    try:
        state = _load_saved_preset()
    except Exception as exc:
        logging.warning("Could not load presets: %s", exc)
        return
    if state is None:
        return

    if state.reapply or state.dynamic:
        daemon.start_auto_reapply(state)
        logging.info(
            "Started: %s (every %ds%s)",
            state.mode, state.interval, ", dynamic" if state.dynamic else "",
        )
    else:
        daemon.apply_preset_state_once(state)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if cfg.get("Info", "Type") == "Intel":
        logging.error("Intel CPUs are not supported.")
        sys.exit(1)

    from Assets.Modules.hardware import _find_dmidecode
    dmi = _find_dmidecode()
    if dmi is None:
        logging.error("dmidecode not found in PATH — hardware detection will fail.")
        sys.exit(1)
    cfg.DMIDECODE = dmi

    logging.info("UXTU4Linux daemon v%s", cfg.LOCAL_VERSION)

    daemon = PowerDaemon()

    if cfg.get("Settings", "ApplyOnStart", "1") == "1":
        _apply_on_start(daemon)

    daemon.run()


if __name__ == "__main__":
    main()
