"""
ui.py - Terminal UI helpers: banner, clear screen, prompts.
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

def clear():
    subprocess.call("clear", shell=True)
    print(BANNER)
    print()
    cpu = cfg.get("Info", "CPU")
    family = cfg.get("Info", "Family")
    if cpu and family:
        print(f"  {cpu} ({family})")
    if cfg.is_debug():
        loaded = cfg.get_loaded_preset()
        if loaded:
            print(f"  Loaded : {loaded}")
        print(f"  Build  : {cfg.LOCAL_BUILD}")
    print(f"  Version: {cfg.LOCAL_VERSION} by HorizonUnix")
    print()

def pause(msg="Press Enter to continue..."):
    input(msg)

def confirm(prompt):
    return input(f"{prompt} (y/n): ").strip().lower() == "y"

def quit_app():
    sys.exit("\nThanks for using UXTU4Unix\nHave a nice day!")