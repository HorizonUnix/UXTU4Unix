"""
daemon.py
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import signal
import subprocess
import sys
import threading
import zmq

_HERE = os.path.dirname(os.path.realpath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Assets.Modules import config as cfg

cfg.load()

_AC_TYPES = frozenset({"Mains", "USB", "USB_C", "USB_PD", "USB_PD_DRP", "USB_C_DRP"})


def _run_cmd(command: str) -> str:
    try:
        args = shlex.split(command)
    except ValueError:
        return ""
    proc = subprocess.Popen(
        args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stdout, _ = proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()


def _on_ac() -> bool:
    ac_online           = False
    found_ac            = False
    battery_discharging = False
    try:
        for entry in os.listdir("/sys/class/power_supply"):
            base = f"/sys/class/power_supply/{entry}"
            try:
                with open(f"{base}/type") as f:
                    ptype = f.read().strip()
            except OSError:
                continue
            if ptype in _AC_TYPES:
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


def _run_ryzenadj(args: str, mode: str) -> str:
    payload = mode.split() if args == "Custom" else args.split()
    result = subprocess.run(
        [cfg.RYZENADJ] + payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = result.stdout.decode(errors="replace")
    if cfg.is_debug() and result.stderr:
        out += result.stderr.decode(errors="replace")
    return out.strip()


def _load_presets() -> dict:
    from Assets.Modules.power import _preset_module_name, _strip_cpu_name
    import importlib

    raw_cpu   = cfg.get("Info", "CPU")
    family    = cfg.get("Info", "Family")
    cpu_type  = cfg.get("Info", "Type")
    cpu_model = _strip_cpu_name(raw_cpu)
    mod_name  = _preset_module_name(cpu_type, family, cpu_model, raw_cpu)
    full_mod  = f"Assets.Presets.{mod_name}"
    module    = importlib.import_module(full_mod)
    cfg.set_loaded_preset(full_mod)
    return module.PRESETS


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
        self._stop_evt.clear()
        while not self._stop_evt.wait(interval):
            eff_mode = mode
            eff_args = args
            if dynamic:
                try:
                    presets  = _load_presets()
                    eff_mode = "Extreme" if _on_ac() else "Eco"
                    eff_args = presets.get(eff_mode, args)
                except Exception as exc:
                    logging.warning("Could not resolve dynamic preset: %s", exc)
            try:
                changed = eff_mode != self._last_logged_mode
                self._apply_once(eff_args, eff_mode, log=changed)
                if changed:
                    self._last_logged_mode = eff_mode
            except Exception as exc:
                logging.warning("Failed to apply preset: %s", exc)
        with self._lock:
            self._running_loop = False

    def _stop_loop(self) -> None:
        self._stop_evt.set()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=self._interval + 2)

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
        args     = msg.get("args", "")
        mode     = msg.get("mode", "Unknown")
        interval = int(msg.get("interval", cfg.get("Settings", "Time", "3")))
        dynamic  = bool(msg.get("dynamic", False))

        self._stop_loop()

        with self._lock:
            self._dynamic      = dynamic
            self._interval     = interval
            self._running_loop = True

        try:
            eff_mode = mode
            eff_args = args
            if dynamic:
                presets  = _load_presets()
                eff_mode = "Extreme" if _on_ac() else "Eco"
                eff_args = presets.get(eff_mode, args)
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
        cfg.load()
        user_mode = cfg.get("User", "Mode")
        try:
            presets = _load_presets()
        except Exception as exc:
            return {"ok": False, "error": f"Could not load presets: {exc}"}

        if user_mode == "Custom":
            args = cfg.get("User", "CustomArgs")
        elif user_mode in presets:
            args = presets[user_mode]
        else:
            return {"ok": False, "error": f"Preset {user_mode!r} not found"}

        reapply  = cfg.get("Settings", "ReApply",     "0") == "1"
        dynamic  = cfg.get("Settings", "DynamicMode", "0") == "1"
        interval = int(float(cfg.get("Settings", "Time", "3")))

        self._stop_loop()

        if reapply or dynamic:
            return self._cmd_apply_loop({
                "args":     args,
                "mode":     user_mode,
                "interval": interval,
                "dynamic":  dynamic,
            })
        return self._cmd_apply({"args": args, "mode": user_mode})

    def _cmd_shutdown(self, _msg: dict) -> dict:
        self._stop_loop()
        return {"ok": True}

    def _cmd_dmidecode(self, msg: dict) -> dict:
        dmi_type = msg.get("type", "")
        if not dmi_type:
            return {"ok": False, "error": "missing 'type'"}
        try:
            out = _run_cmd(f"{cfg.DMIDECODE} -t {dmi_type}")
            return {"ok": True, "output": out}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    _DISPATCH = {
        "ping":        "_cmd_ping",
        "apply":       "_cmd_apply",
        "apply_loop":  "_cmd_apply_loop",
        "stop_loop":   "_cmd_stop_loop",
        "status":      "_cmd_status",
        "apply_saved": "_cmd_apply_saved",
        "shutdown":    "_cmd_shutdown",
        "dmidecode":   "_cmd_dmidecode",
    }

    def handle(self, raw: str) -> str:
        try:
            msg    = json.loads(raw)
            cmd    = msg.get("cmd", "")
            method = self._DISPATCH.get(cmd)
            if method:
                resp = getattr(self, method)(msg)
            else:
                resp = {"ok": False, "error": f"unknown command: {cmd!r}"}
        except Exception as exc:
            resp = {"ok": False, "error": str(exc)}
        return json.dumps(resp)

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
            os.chmod(cfg.ZMQ_SOCKET_PATH, 0o666)

        logging.info("Listening on %s", cfg.ZMQ_SOCKET_ADDR)

        def _sig_handler(*_):
            logging.info("Shutting down.")
            self._stop_loop()
            if os.path.exists(cfg.ZMQ_SOCKET_PATH):
                os.unlink(cfg.ZMQ_SOCKET_PATH)
            sock.close()
            ctx.term()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _sig_handler)
        signal.signal(signal.SIGINT,  _sig_handler)

        while True:
            raw  = sock.recv_string()
            resp = self.handle(raw)
            sock.send_string(resp)
            if json.loads(raw).get("cmd") == "shutdown":
                logging.info("Shutdown command received.")
                break

        if os.path.exists(cfg.ZMQ_SOCKET_PATH):
            os.unlink(cfg.ZMQ_SOCKET_PATH)
        sock.close()
        ctx.term()


def _apply_on_start(daemon: PowerDaemon) -> None:
    user_mode = cfg.get("User", "Mode")
    try:
        presets = _load_presets()
    except Exception as exc:
        logging.warning("Could not load presets: %s", exc)
        return

    if user_mode == "Custom":
        args = cfg.get("User", "CustomArgs")
    elif user_mode in presets:
        args = presets[user_mode]
    else:
        logging.warning("Saved preset %r not found.", user_mode)
        return

    reapply  = cfg.get("Settings", "ReApply",     "0") == "1"
    dynamic  = cfg.get("Settings", "DynamicMode", "0") == "1"
    interval = int(float(cfg.get("Settings", "Time", "3")))

    if reapply or dynamic:
        daemon._cmd_apply_loop({
            "args":     args,
            "mode":     user_mode,
            "interval": interval,
            "dynamic":  dynamic,
        })
        logging.info(
            "Started: %s (every %ds%s)",
            user_mode, interval, ", dynamic" if dynamic else "",
        )
    else:
        daemon._apply_once(args, user_mode, log=True)


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

    logging.info("UXTU4Unix daemon v%s", cfg.LOCAL_VERSION)

    daemon = PowerDaemon()

    if cfg.get("Settings", "ApplyOnStart", "1") == "1":
        _apply_on_start(daemon)

    daemon.run()


if __name__ == "__main__":
    main()
