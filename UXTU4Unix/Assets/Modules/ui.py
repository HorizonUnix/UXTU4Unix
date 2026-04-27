"""
ui.py - Terminal UI helpers: banner, clear screen, common prompts.
"""
import subprocess
import sys

from . import config as cfg

BANNER = r"""
+----------------------------------------------------+
|  _   ___  _______ _   _ _  _   _   _       _       |
| | | | \ \/ /_   _| | | | || | | | | |_ __ (_)_  __ |
| | | | |\  /  | | | | | | || |_| | | | '_ \| \ \/ / |
| | |_| |/  \  | | | |_| |__   _| |_| | | | | |>  <  |
|  \___//_/\_\ |_|  \___/   |_|  \___/|_| |_|_/_/\_\ |
+----------------------------------------------------+"""


def clear() -> None:
    """Clear the terminal and redraw the banner."""
    subprocess.call("clear", shell=True)
    print(BANNER)
    print()

    cpu    = cfg.get("Info", "CPU")
    family = cfg.get("Info", "Family")
    if cpu and family:
        print(f"  {cpu} ({family})")

    if cfg.is_debug():
        print(f"  Loaded : {cfg.get('User', 'Preset')}")
        print(f"  Build  : {cfg.LOCAL_BUILD}")          # type: ignore[attr-defined]

    print(f"  Version: {cfg.LOCAL_VERSION} by HorizonUnix")   # type: ignore[attr-defined]
    print()


def pause(msg: str = "Press Enter to continue...") -> None:
    input(msg)


def confirm(prompt: str) -> bool:
    """Return True when the user answers 'y'."""
    return input(f"{prompt} (y/n): ").strip().lower() == "y"


def menu(title: str, options: dict[str, tuple[str, object]], *, hint: str = "") -> None:
    """
    Generic interactive menu loop.

    options format:
        key -> (label, callable | "break" | None)

    A key mapped to "break" exits the loop.
    A key mapped to None is a no-op (display-only separator).
    """
    while True:
        clear()
        print(f"{'-' * 15} {title} {'-' * 15}")
        for key, (label, _) in options.items():
            if label:
                print(f"{key.upper()}. {label}")
        if hint:
            print(f"\n{hint}")
        print()
        choice = input("Option: ").strip().lower()
        action = options.get(choice)
        if action is None:
            print("Invalid option.")
            pause()
            continue
        _, fn = action
        if fn == "break":
            break
        if callable(fn):
            fn()


def quit_app() -> None:
    sys.exit("\nThanks for using UXTU4Unix\nHave a nice day!")