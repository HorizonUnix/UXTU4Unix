"""
about.py - About screen and forced-update entry point.
"""
import webbrowser
from . import config as cfg
from .updater import get_latest_version, show_updater
from .ui import clear, pause


def about_menu():
    while True:
        clear()
        print("-" * 15 + " About UXTU4Unix " + "-" * 15)
        print("Maintainer : oxGorou")
        print("CLI        : oxGorou")
        print("Advisor    : NotchApple1703")
        if cfg.KERNEL == "Darwin":
            print("dmidecode  : Acidanthera")
            print("CMD file   : CorpNewt")
        print()
        print("  1. Open GitHub page")
        has_latest = False
        try:
            latest = get_latest_version()
            print(f"  F. Force update to {latest}")
            has_latest = True
        except Exception:
            pass
        print("\n  B. Back\n")
        c = input("Option: ").strip().lower()
        match c:
            case "1":
                webbrowser.open("https://www.github.com/HorizonUnix/UXTU4Unix")
            case "f" if has_latest:
                show_updater()
                return
            case "b":
                break
            case _:
                print("Invalid option.")
                pause()