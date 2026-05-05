"""
ipc.py
"""

from __future__ import annotations

import json
import zmq

from . import config as cfg


class DaemonClient:
    TIMEOUT_MS = 5_000

    def __init__(self, addr: str = cfg.ZMQ_SOCKET_ADDR) -> None:
        self._addr = addr

    def _send(self, cmd: dict) -> dict | None:
        ctx  = zmq.Context.instance()
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.RCVTIMEO, self.TIMEOUT_MS)
        sock.setsockopt(zmq.SNDTIMEO, self.TIMEOUT_MS)
        sock.setsockopt(zmq.LINGER, 0)
        sock.connect(self._addr)
        try:
            sock.send_string(json.dumps(cmd))
            return json.loads(sock.recv_string())
        except zmq.ZMQError:
            return None
        finally:
            sock.close()

    def ping(self) -> bool:
        r = self._send({"cmd": "ping"})
        return r is not None and r.get("ok", False)

    def apply(self, args: str, mode: str) -> dict:
        return self._send({"cmd": "apply", "args": args, "mode": mode}) \
            or {"ok": False, "error": "daemon not responding"}

    def apply_loop(self, args: str, mode: str, interval: int, dynamic: bool) -> dict:
        return self._send({
            "cmd":      "apply_loop",
            "args":     args,
            "mode":     mode,
            "interval": interval,
            "dynamic":  dynamic,
        }) or {"ok": False, "error": "daemon not responding"}

    def stop_loop(self) -> dict:
        return self._send({"cmd": "stop_loop"}) or {"ok": False}

    def status(self) -> dict:
        return self._send({"cmd": "status"}) or {
            "ok": False, "running_loop": False, "mode": "?", "on_ac": False,
        }

    def apply_saved(self) -> dict:
        return self._send({"cmd": "apply_saved"}) \
            or {"ok": False, "error": "daemon not responding"}

    def shutdown(self) -> dict:
        return self._send({"cmd": "shutdown"}) or {"ok": False}

    def dmidecode(self, dmi_type: str) -> str:
        r = self._send({"cmd": "dmidecode", "type": dmi_type})
        if r and r.get("ok"):
            return r["output"]
        return ""


_client: DaemonClient | None = None


def get_client() -> DaemonClient:
    global _client
    if _client is None:
        _client = DaemonClient()
    return _client


def require_daemon() -> DaemonClient:
    client = get_client()
    if not client.ping():
        raise RuntimeError(
            "Daemon is not running.\n"
            "Enable it with:  sudo systemctl enable --now uxtu4linux.service"
        )
    return client