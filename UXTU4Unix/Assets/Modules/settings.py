"""
settings.py
"""
from __future__ import annotations
import getpass, subprocess
from . import config as cfg
from .power import apply_smu, get_presets, _daemon_apply_saved
from .keyring import save_password, has_password
from .ui import menu, clear, ask, pause, confirm


def _tog(section: str, key: str, default: str = "0") -> str:
    return "ON" if cfg.get(section, key, default) == "1" else "OFF"


def _verify_sudo(pw: str) -> bool:
    subprocess.run("sudo -k", shell=True)
    r = subprocess.run(
        ["sudo", "-S", "ls", "/"],
        input=pw.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return r.returncode == 0


_TOGGLE_MAP = {
    "Apply preset on daemon start":  ("Settings", "ApplyOnStart",   "1", False),
    "Software update": ("Settings", "SoftwareUpdate", "1", False),
    "Debug":           ("Settings", "Debug",          "1", False),
}


def _do_toggle(idx: int, items: list) -> None:
    lbl = items[idx][0]
    if lbl not in _TOGGLE_MAP:
        return
    section, key, default, notify = _TOGGLE_MAP[lbl]
    was_on = cfg.get(section, key, default) == "1"
    cfg.set(section, key, "0" if was_on else "1")
    cfg.save()
    items[idx] = (lbl, "OFF" if was_on else "ON", "toggle")
    if notify:
        _daemon_apply_saved()


def _settings_items() -> list:
    from .setup import service_running
    running = service_running()
    return [
        ("Daemon service",   "Running" if running else "Stopped"),
        ("─", "", "sep"),
        ("Apply preset on daemon start",   _tog("Settings", "ApplyOnStart",  "1"),  "toggle"),
        ("Software update",  _tog("Settings", "SoftwareUpdate","1"),  "toggle"),
        ("Debug",            _tog("Settings", "Debug",         "1"),  "toggle"),
        ("─", "", "sep"),
        ("Sudo password",    "Set" if has_password() else "Not set"),
        ("Reset all",        ""),
        ("Back",             ""),
    ]


def settings_menu() -> None:
    from .setup import daemon_menu

    last_idx = 0
    while True:
        items  = _settings_items()
        choice = menu("Settings", items, selected=last_idx, on_toggle=_do_toggle)
        if choice == -1:
            return

        last_idx = choice
        lbl = items[choice][0]

        if lbl == "Back":
            return
        elif lbl == "Daemon service":
            daemon_menu()
        elif lbl in _TOGGLE_MAP:
            _do_toggle(choice, items)
        elif lbl == "Sudo password":
            pass_cfg()
        elif lbl == "Reset all":
            _reset_all()


def preset_cfg() -> None:
    presets = get_presets()
    names   = list(presets.keys())

    items = (
        [("Dynamic mode (recommended)", "auto AC/battery")]
        + [(n, "") for n in names]
        + [("Custom", "manual ryzenadj args"), ("Back", "")]
    )

    while True:
        choice = menu("Choose a preset", items, subtitle="You can change this later in Power Management")
        if choice == -1 or items[choice][0] == "Back":
            return

        lbl = items[choice][0]

        if lbl == "Dynamic mode (recommended)":
            cfg.set("User",     "Mode",        "Balance")
            cfg.set("Settings", "DynamicMode", "1")
            cfg.set("Settings", "ReApply",     "1")
            cfg.save()
            return
        elif lbl == "Custom":
            args = ask("ryzenadj arguments")
            if args:
                cfg.set("User",     "Mode",        "Custom")
                cfg.set("User",     "CustomArgs",  args)
                cfg.set("Settings", "DynamicMode", "0")
                cfg.save()
            return
        elif lbl in names:
            cfg.set("User",     "Mode",        lbl)
            cfg.set("Settings", "DynamicMode", "0")
            cfg.save()
            return


def sleep_cfg() -> None:
    clear()
    current = cfg.get("Settings", "Time", "3")
    val = ask("Reapply interval in seconds", default=current)
    if val.isdigit():
        cfg.set("Settings", "Time", val)
        cfg.save()
        _daemon_apply_saved()
    else:
        print("\n  Must be a whole number.")
        pause()


def pass_cfg() -> None:
    while True:
        subtitle = f"Stored: {'Yes (keyring)' if has_password() else 'Not set'}"
        items    = [("Change password", ""), ("Back", "")]
        choice   = menu("Sudo Password", items, subtitle=subtitle)
        if choice == -1 or items[choice][0] == "Back":
            return

        clear()
        while True:
            pw = getpass.getpass("  New sudo password: ")
            if _verify_sudo(pw):
                save_password(pw)
                print("  Password saved.")
                pause()
                return
            print("  Incorrect — try again.")


def _reset_all() -> None:
    clear()
    if confirm("Reset all settings? This cannot be undone"):
        from .setup import reset_all
        reset_all()