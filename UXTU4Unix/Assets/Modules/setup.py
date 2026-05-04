"""
setup.py
"""

from __future__ import annotations
import os, re, subprocess, sys, tempfile, time
from . import config as cfg
from .hardware import detect as detect_hardware
from .ui import clear, pause, confirm, menu

SERVICE_NAME = "uxtu4unix.service"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}"


def _ensure_venv() -> None:
    venv_dir    = cfg.VENV_DIR
    venv_python = cfg.VENV_PYTHON

    def _sudo(*args: str) -> int:
        return subprocess.run(["sudo", *args]).returncode

    if not os.path.isfile(venv_python):
        print(f"  Creating venv at {venv_dir}...")
        _sudo("mkdir", "-p", venv_dir)
        if _sudo(sys.executable, "-m", "venv", "--without-pip", venv_dir) != 0:
            print("  Failed to create venv.")
            pause()
            return
        if _sudo(venv_python, "-m", "ensurepip", "--upgrade") != 0:
            print("  Failed to bootstrap pip.")
            pause()
            return

    probe = subprocess.run(
        [venv_python, "-c", "import zmq"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        print("  Installing pyzmq...")
        if _sudo(venv_python, "-m", "pip", "install", "pyzmq", "--quiet") != 0:
            print("  Failed to install pyzmq.")
            pause()
            return


def _daemon_script() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "daemon.py")


def _python() -> str:
    return cfg.VENV_PYTHON if os.path.isfile(cfg.VENV_PYTHON) else sys.executable


def _render_unit() -> str:
    return (
        "[Unit]\n"
        "Description=UXTU4Unix Power Management Daemon\n"
        "After=multi-user.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={_python()} {_daemon_script()}\n"
        "Restart=on-failure\n"
        "RestartSec=5\n"
        "StandardOutput=journal\n"
        "StandardError=journal\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )


def _sudo_run(*args: str) -> int:
    return subprocess.run(["sudo", *args]).returncode


def _systemctl(*args: str) -> int:
    return _sudo_run("systemctl", *args)


def _sudo_write(path: str, content: str) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        r = subprocess.run(["sudo", "mv", tmp, path])
        return r.returncode == 0
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _wait_for_daemon(timeout: float = 10.0, interval: float = 0.3) -> bool:
    from .ipc import get_client
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if get_client().ping():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def install_service() -> None:
    _ensure_venv()
    if not _sudo_write(SERVICE_FILE, _render_unit()):
        print("  Failed to write service file.")
        return
    _systemctl("daemon-reload")
    _systemctl("enable", SERVICE_NAME)
    _systemctl("start",  SERVICE_NAME)


def uninstall_service() -> None:
    _systemctl("stop",    SERVICE_NAME)
    _systemctl("disable", SERVICE_NAME)
    _sudo_run("rm", "-f", SERVICE_FILE)
    _systemctl("daemon-reload")


def service_running() -> bool:
    return subprocess.call(
        ["systemctl", "is-active", "--quiet", SERVICE_NAME],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) == 0


def service_enabled() -> bool:
    return subprocess.call(
        ["systemctl", "is-enabled", "--quiet", SERVICE_NAME],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) == 0


def restart_service() -> None:
    _systemctl("restart", SERVICE_NAME)


def show_logs() -> None:
    subprocess.call(["journalctl", "-u", SERVICE_NAME, "-n", "50", "--no-pager"])


def verify_service_path() -> None:
    if not os.path.isfile(SERVICE_FILE):
        return
    current = _daemon_script()
    try:
        content = open(SERVICE_FILE).read()
    except OSError:
        return
    for line in content.splitlines():
        if not line.startswith("ExecStart="):
            continue
        parts = line.split()
        if len(parts) < 3:
            break
        installed = parts[2]
        if installed == current:
            break
        print(f"  Service path stale (app was moved).")
        print(f"  Was: {installed}")
        print(f"  Now: {current}")
        new = re.sub(
            r"(ExecStart=\S+\s+)\S+",
            lambda m: m.group(1) + current,
            content,
        )
        if _sudo_write(SERVICE_FILE, new):
            _systemctl("daemon-reload")
            _systemctl("restart", SERVICE_NAME)
            print("  Service file updated and daemon restarted.")
        else:
            print(f"  Update manually: sudo nano {SERVICE_FILE}")
        pause()
        break


def daemon_menu() -> None:
    while True:
        running  = service_running()
        enabled  = service_enabled()
        subtitle = (
            f"Status: {'Running' if running else 'Stopped'}\n"
            f"{'Enabled on boot' if enabled else 'Not enabled'}"
        )
        items = [
            ("Install & enable", ""),
            ("Uninstall",        ""),
            ("Restart",          ""),
            ("View logs",        "last 50 lines"),
            ("Back",             ""),
        ]
        choice = menu("Daemon Service", items, subtitle=subtitle)
        if choice == -1 or items[choice][0] == "Back":
            return

        lbl = items[choice][0]
        clear()
        if lbl == "Install & enable":
            install_service()
            print("  Waiting for daemon...", end="", flush=True)
            if _wait_for_daemon():
                print(" ready.")
            else:
                print("\n  Warning: daemon did not start in time.")
            pause()
        elif lbl == "Uninstall":
            uninstall_service()
            print("  Service removed.")
            pause()
        elif lbl == "Restart":
            restart_service()
            print("  Service restarted.")
            pause()
        elif lbl == "View logs":
            show_logs()
            pause()


def ensure_binaries_executable() -> None:
    for path in [cfg.RYZENADJ]:
        if path and os.path.isfile(path) and not os.access(path, os.X_OK):
            try:
                subprocess.run(["chmod", "+x", path], check=True)
            except subprocess.CalledProcessError:
                pass


def _apply_defaults() -> None:
    cfg.ensure_sections("User", "Settings", "Info")
    cfg.set("Settings", "Time",           "3")
    cfg.set("Settings", "SoftwareUpdate", "1")
    cfg.set("Settings", "ReApply",        "0")
    cfg.set("Settings", "ApplyOnStart",   "1")
    cfg.set("Settings", "DynamicMode",    "0")
    cfg.set("Settings", "Debug",          "1")


def _step(n: int, total: int, title: str) -> None:
    clear()
    print(f"  Step {n}/{total}  —  {title}\n")


def run_welcome() -> None:
    if cfg.KERNEL not in ("Linux",):
        clear()
        print(f"  Unsupported OS: {cfg.KERNEL}")
        return

    cfg.ensure_sections("User", "Settings", "Info")
    TOTAL = 3

    _step(1, TOTAL, "Welcome")
    print("  UXTU4Unix — AMD Zen power management for Linux")
    print("  Built on RyzenAdj — inspired by UXTU\n")
    pause()

    _step(2, TOTAL, "Daemon service")
    _apply_defaults()
    ensure_binaries_executable()
    cfg.save()
    print("  The power daemon runs in the background keeping your preset active.")
    print("  It is required for UXTU4Unix to work properly.\n")
    if confirm("Install and enable daemon service"):
        if service_running():
            restart_service()
        else:
            install_service()
        print("\n  Waiting for daemon...", end="", flush=True)
        if _wait_for_daemon():
            print(" ready.")
        else:
            print("\n  Warning: daemon did not start in time.")
            print("  Hardware detection may fail — check logs if issues occur.")
    else:
        print("\n  Daemon is required. Exiting setup.")
        pause()
        return
        
    pause()

    _step(3, TOTAL, "Hardware detection")
    print("  Detecting hardware...\n")
    detect_hardware()

    cpu      = cfg.get("Info", "CPU")
    family   = cfg.get("Info", "Family")
    arch     = cfg.get("Info", "Architecture")
    cpu_type = cfg.get("Info", "Type")
    sig      = cfg.get("Info", "Signature")

    W = 14
    def row(label: str, value: str) -> None:
        print(f"  \033[2m{label:<{W}}\033[0m  {value}")

    row("CPU",      cpu      or "Not detected")
    row("Family",   family   or "Unknown")
    row("Arch",     arch     or "Unknown")
    row("Type",     cpu_type or "Unknown")
    row("Signature",sig      or "Unknown")
    
    print()
    pause()

    clear()
    print("  Setup complete. UXTU4Unix is ready.\n")
    pause()


def check_integrity() -> None:
    if not os.path.isfile(cfg.CONFIG_PATH) or os.stat(cfg.CONFIG_PATH).st_size == 0:
        run_welcome()
        return

    cfg.load()

    broken = (
        any(not cfg.instance().has_section(s) for s in cfg.REQUIRED)
        or any(
            k not in cfg.instance()[s]
            for s, keys in cfg.REQUIRED.items()
            if cfg.instance().has_section(s)
            for k in keys
        )
    )
    if broken:
        reset_all()


def reset_all() -> None:
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    cfg.load()
    run_welcome()