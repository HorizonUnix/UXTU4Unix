"""
setup.py
"""

from __future__ import annotations
import getpass, os, re, subprocess, sys, tempfile
from . import config as cfg
from .hardware import detect as detect_hardware
from .keyring import (
    backend_available, delete_password,
    get_password, has_password, save_password,
)
from .ui import clear, pause, confirm, ask, menu

SERVICE_NAME = "uxtu4unix.service"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}"


def _ensure_venv() -> None:
    password    = (get_password() or "").encode()
    venv_dir    = cfg.VENV_DIR
    venv_python = cfg.VENV_PYTHON

    def _sudo(*args: str) -> int:
        return subprocess.run(
            ["sudo", "-S", *args],
            input=password,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

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
    password = (get_password() or "").encode()
    return subprocess.run(
        ["sudo", "-S", *args],
        input=password,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def _systemctl(*args: str) -> int:
    return _sudo_run("systemctl", *args)


def _sudo_write(path: str, content: str) -> bool:
    password = (get_password() or "").encode()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        r = subprocess.run(
            ["sudo", "-S", "mv", tmp, path],
            input=password,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return r.returncode == 0
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def install_service() -> None:
    _ensure_venv()
    if not _sudo_write(SERVICE_FILE, _render_unit()):
        print("  Failed to write service file.")
        print("  Check sudo password in Settings.")
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
            print("  Service installed and started.")
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


def _prompt_sudo() -> None:
    while True:
        subprocess.run("sudo -k", shell=True)
        pw = getpass.getpass("  Sudo (login) password: ")
        r  = subprocess.run(
            ["sudo", "-S", "ls", "/"],
            input=pw.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if r.returncode == 0:
            save_password(pw)
            return
        print("  Incorrect — try again.")


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
    TOTAL = 5

    _step(1, TOTAL, "Welcome")
    print("  UXTU4Unix — AMD Zen power management for Linux")
    print("  Built on RyzenAdj — inspired by UXTU\n")
    pause()

    _step(2, TOTAL, "Keyring")
    print("  Checking secret service backend...")
    if not backend_available():
        print("\n  No keyring found.")
        print("  Install gnome-keyring or kwallet, then restart UXTU4Unix.")
        sys.exit(1)
    print("  Keyring OK.")
    pause()

    _step(3, TOTAL, "Sudo password")
    _prompt_sudo()
    _apply_defaults()
    ensure_binaries_executable()
    cfg.save()

    _step(4, TOTAL, "Hardware detection")
    print("  Detecting hardware...")
    detect_hardware()
    pause()

    from .settings import preset_cfg
    preset_cfg()

    _step(5, TOTAL, "Daemon service")
    if not service_running():
        print("  The power daemon runs in the background keeping your preset active.")
        print("  It is required for UXTU4Unix to work properly.\n")
        if confirm("Install and enable daemon service"):
            install_service()
            print("\n  Daemon installed and started.")
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
        return

    if not has_password():
        print("  Warning: sudo password not found in keyring.")
        print("  Go to Settings → Sudo password.")
        pause()


def reset_all() -> None:
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    delete_password()
    cfg.load()
    run_welcome()