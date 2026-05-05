"""
ui.py
"""

from __future__ import annotations
import os, select, subprocess, sys, termios, tty
from dataclasses import dataclass
from typing import Literal
from . import config as cfg

BANNER = """
██╗   ██╗██╗  ██╗████████╗██╗   ██╗██╗  ██╗██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗
██║   ██║╚██╗██╔╝╚══██╔══╝██║   ██║██║  ██║██║     ██║████╗  ██║██║   ██║╚██╗██╔╝
██║   ██║ ╚███╔╝    ██║   ██║   ██║███████║██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝ 
██║   ██║ ██╔██╗    ██║   ██║   ██║╚════██║██║     ██║██║╚██╗██║██║   ██║ ██╔██╗ 
╚██████╔╝██╔╝ ██╗   ██║   ╚██████╔╝     ██║███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝      ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝ """

_R   = "\033[0m"
_B   = "\033[1m"
_D   = "\033[2m"
_C   = "\033[96m"
HIDE = "\033[?25l"
SHOW = "\033[?25h"

UP    = b"\x1b[A"
DOWN  = b"\x1b[B"
ENTER = b"\r"
ESC   = b"\x1b"

Kind = Literal["action", "toggle", "separator"]

@dataclass
class MenuItem:
    label: str
    hint:  str  = ""
    kind:  Kind = "action"


def _getch() -> bytes:
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                ch += os.read(fd, 3)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _draw(lines: list[str], prev: int) -> int:
    if prev:
        sys.stdout.write(f"\x1b[{prev}A\x1b[J")
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()
    return len(lines)


def clear() -> None:
    subprocess.call("clear", shell=True)
    print(f"{_C}{BANNER}{_R}")
    print(f" {'─' * 80}")
    cpu    = cfg.get("Info", "CPU")
    family = cfg.get("Info", "Family")
    if cpu and family:
        print(f"  {_B}{cpu}{_R} {_D}{family}{_R}")
    if cfg.is_debug():
        loaded = cfg.get_loaded_preset()
        if loaded:
            print(f"  {_D}Loaded : {loaded}{_R}")
        print(f"  {_D}Build  : {cfg.LOCAL_BUILD}{_R}")
    print(f"  {_D}v{cfg.LOCAL_VERSION} by HorizonUnix{_R}\n")


def pause(msg: str = "Press Enter to continue...") -> None:
    input(f"  {_D}{msg}{_R} ")


def confirm(prompt: str) -> bool:
    return input(f"\n  {prompt} (y/n): ").strip().lower() == "y"


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val  = input(f"\n  {prompt}{_D}{hint}{_R}: ").strip()
    return val or default


def quit_app() -> None:
    sys.stdout.write(SHOW)
    sys.exit(f"\n  Thanks for using UXTU4Unix\n  Have a nice day!\n")


def _label(item) -> str:
    if isinstance(item, MenuItem):
        return item.label
    return item[0] if isinstance(item, (tuple, list)) else str(item)


def _hint(item) -> str:
    if isinstance(item, MenuItem):
        return item.hint
    return item[1] if isinstance(item, (tuple, list)) and len(item) > 1 else ""


def _tag(item) -> str:
    if isinstance(item, MenuItem):
        return item.kind if item.kind in ("toggle", "separator") else ""
    return item[2] if isinstance(item, (tuple, list)) and len(item) > 2 else ""


def _is_sep(item) -> bool:
    if isinstance(item, MenuItem):
        return item.kind == "separator"
    return _tag(item) == "sep" or _label(item).startswith("─")


def _clamp_skip(idx: int, items: list) -> int:
    n = len(items)
    if n == 0:
        return 0
    idx = max(0, min(idx, n - 1))
    for delta in range(n):
        i = (idx + delta) % n
        if not _is_sep(items[i]):
            return i
    return idx


def _step(idx: int, d: int, items: list) -> int:
    n = len(items)
    for _ in range(n):
        idx = (idx + d) % n
        if not _is_sep(items[idx]):
            return idx
    return idx


def render_menu(title: str, subtitle: str, items: list, idx: int) -> list[str]:
    lines: list[str] = []
    lines.append(f"  {_B}{title}{_R}")
    if subtitle:
        for sub_line in subtitle.split("\n"):
            lines.append(f"  {_D}{sub_line}{_R}")
    lines.append("")
    for i, item in enumerate(items):
        if _is_sep(item):
            lines.append(f"  {_D}{'─' * 40}{_R}")
            continue
        lbl  = _label(item)
        hint = _hint(item)
        h    = f"  {_D}{hint}{_R}" if hint else ""
        if i == idx:
            lines.append(f"  {_C}▶{_R} {_B}{lbl}{_R}{h}")
        else:
            lines.append(f"    {_D}{lbl}{_R}{h}")
    lines.append("")
    lines.append(f"  {_D}↑/↓ to navigate, Enter to select, Esc to go back{_R}")
    return lines


def menu(
    title:     str,
    items:     list,
    *,
    subtitle:  str = "",
    selected:  int = 0,
    on_toggle       = None,
) -> int:
    clear()
    sys.stdout.write(HIDE)
    sys.stdout.flush()
    idx  = _clamp_skip(selected, items)
    prev = 0
    try:
        while True:
            lines = render_menu(title, subtitle, items, idx)
            prev  = _draw(lines, prev)
            key   = _getch()
            if key == b"\x03":
                sys.stdout.write(SHOW + "\n")
                sys.exit(0)
            elif key == UP:
                idx = _step(idx, -1, items)
            elif key == DOWN:
                idx = _step(idx, +1, items)
            elif key in (ENTER, b"\n"):
                if on_toggle and _tag(items[idx]) == "toggle":
                    on_toggle(idx, items)
                    clear()
                    sys.stdout.write(HIDE)
                    sys.stdout.flush()
                    prev = 0
                else:
                    sys.stdout.write("\n")
                    return idx
            elif key == ESC:
                sys.stdout.write("\n")
                return -1
    finally:
        sys.stdout.write(SHOW)
        sys.stdout.flush()


def about_menu() -> None:
    import webbrowser
    from .updater import get_latest_version, show_updater

    while True:
        latest = None
        try:
            latest = get_latest_version()
        except Exception:
            pass

        items: list[MenuItem] = [MenuItem("Open GitHub page")]
        if latest:
            items.append(MenuItem("Force update", hint=f"→ {latest}"))
        items.append(MenuItem("Back"))

        subtitle = "Maintainer: oxGorou\nAdvisor: NotchApple1703"
        choice   = menu("About UXTU4Unix", items, subtitle=subtitle)

        if choice == -1 or items[choice].label == "Back":
            return
        elif items[choice].label == "Open GitHub page":
            webbrowser.open("https://www.github.com/HorizonUnix/UXTU4Unix")
        elif items[choice].label.startswith("Force update") and latest:
            show_updater()
            return