#!/usr/bin/env python3
import os, subprocess, sys

_ROOT = os.path.dirname(os.path.realpath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Assets.Modules import config as cfg
cfg.load()

from Assets.Modules.hardware  import check_binaries, check_system_compat, show_info as hardware_info
from Assets.Modules.power     import apply_smu, get_presets, preset_menu
from Assets.Modules.settings  import settings_menu
from Assets.Modules.setup     import (
    check_integrity, ensure_binaries_executable,
    run_welcome, service_running, verify_service_path,
)
from Assets.Modules.updater   import check_updates
from Assets.Modules.ui        import clear, pause, quit_app, menu, about_menu


def _require_daemon() -> None:
    from Assets.Modules.ipc   import get_client
    from Assets.Modules.setup import daemon_menu

    client = get_client()
    if client.ping():
        return

    clear()
    print("  The UXTU4Unix daemon is not running.\n")
    print("  It needs to be installed as a system service.\n")
    pause("Press Enter to open the daemon setup menu...")
    daemon_menu()

    if not client.ping():
        clear()
        print("  Daemon still not running. Exiting.")
        pause()
        sys.exit(1)


def _apply_on_start() -> None:
    from Assets.Modules.ipc import get_client

    client = get_client()
    if not client.ping():
        return

    if client.status().get("running_loop"):
        return

    presets   = get_presets()
    user_mode = cfg.get("User", "Mode")

    if user_mode == "Custom":
        apply_smu(cfg.get("User", "CustomArgs"), "Custom")
    elif user_mode in presets:
        apply_smu(presets[user_mode], user_mode)
    else:
        clear()
        print("  Saved preset not found — running setup.")
        pause()
        run_welcome()


def main() -> None:
    subprocess.run("printf '\\e[8;35;80t'", shell=True)

    check_integrity()
    check_binaries()
    ensure_binaries_executable()
    check_system_compat()

    if cfg.get("Settings", "SoftwareUpdate", "0") == "1":
        check_updates()

    verify_service_path()
    _require_daemon()

    try:
        get_presets()
    except Exception:
        pass

    _apply_on_start()

    items = [
        ("Power Management",    ""),
        ("Settings",            ""),
        ("Hardware information",""),
        ("About",               ""),
        ("Quit",                ""),
    ]

    actions = [preset_menu, settings_menu, hardware_info, about_menu, quit_app]

    while True:
        choice = menu("Menu", items)
        if choice == -1:
            quit_app()
        actions[choice]()


if __name__ == "__main__":
    main()