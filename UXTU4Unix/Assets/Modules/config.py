"""
config.py - Central configuration management for UXTU4Unix.
Handles constants, file paths, and config read/write operations.
"""

import os
import sys
from configparser import ConfigParser

# Version info
LOCAL_VERSION  = "0.5.1"
LOCAL_BUILD    = "5Universal270426Rev1"
VERSION_DESC   = "The Refractor Update"
GITHUB_API_URL = "https://api.github.com/repos/HorizonUnix/UXTU4Unix/releases/latest"
LATEST_VER_URL = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest"

# config.py lives at  Assets/Modules/config.py
# _ROOT is the project root (two levels up from Modules/)
_ROOT      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ASSETS_DIR = os.path.join(_ROOT, "Assets")
CONFIG_PATH = os.path.join(ASSETS_DIR, "config.toml")
MODULES_DIR = os.path.join(ASSETS_DIR, "Modules")
PRESETS_DIR = os.path.join(ASSETS_DIR, "Presets")

KERNEL = os.uname().sysname   # "Darwin" | "Linux"

if KERNEL == "Darwin":
    RYZENADJ  = os.path.join(ASSETS_DIR, "Darwin", "ryzenadj")
    DMIDECODE = os.path.join(ASSETS_DIR, "Darwin", "dmidecode")
    # macOS is launched via a .command shell-script wrapper whose name is fixed
    CMD_FILE  = os.path.join(_ROOT, "UXTU4Unix.command")
else:
    RYZENADJ  = os.path.join(ASSETS_DIR, "Linux", "ryzenadj")
    DMIDECODE = "dmidecode"
    CMD_FILE  = os.path.realpath(sys.argv[0])

_cfg = ConfigParser()

_loaded_preset: str = ""

def set_loaded_preset(name: str) -> None:
    global _loaded_preset
    _loaded_preset = name

def get_loaded_preset() -> str:
    return _loaded_preset

def load() -> ConfigParser:
    """Read config from disk and return the singleton."""
    _cfg.read(CONFIG_PATH)
    return _cfg


def get(section: str, key: str, fallback: str = "") -> str:
    return _cfg.get(section, key, fallback=fallback)


def set(section: str, key: str, value: str) -> None:
    if not _cfg.has_section(section):
        _cfg.add_section(section)
    _cfg.set(section, key, value)


def save() -> None:
    with open(CONFIG_PATH, "w") as fh:
        _cfg.write(fh)


def ensure_sections(*sections: str) -> None:
    for s in sections:
        if not _cfg.has_section(s):
            _cfg.add_section(s)


def is_debug() -> bool:
    return get("Settings", "Debug", "1") == "1"


def instance() -> ConfigParser:
    """Return raw ConfigParser instance for direct access."""
    return _cfg


# Required config keys for integrity check
REQUIRED = {
    "User":     ["mode"],
    "Settings": ["time", "dynamicmode", "reapply", "applyonstart",
                 "softwareupdate", "debug"],
    "Info":     ["cpu", "signature", "architecture", "family", "type"],
}
if KERNEL == "Darwin":
    REQUIRED["Settings"].append("sip")