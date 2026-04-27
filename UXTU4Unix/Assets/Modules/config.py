"""
config.py - Central configuration management for UXTU4Unix.
Handles constants, file paths, and config read/write operations.
"""

import os
from configparser import ConfigParser

# Version info
LOCAL_VERSION     = "0.5.0"
LOCAL_BUILD       = "5Universal270426"
VERSION_DESC      = "The Refractor Update"
GITHUB_API_URL    = "https://api.github.com/repos/HorizonUnix/UXTU4Unix/releases/latest"
LATEST_VER_URL    = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest"

# Paths
_ROOT         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ASSETS_DIR    = os.path.join(_ROOT, "Assets")
CONFIG_PATH   = os.path.join(ASSETS_DIR, "config.toml")
MODULES_DIR   = os.path.join(ASSETS_DIR, "Modules")
PRESETS_DIR   = os.path.join(ASSETS_DIR, "Presets")

KERNEL = os.uname().sysname

if KERNEL == "Darwin":
    RYZENADJ  = os.path.join(ASSETS_DIR, "Darwin", "ryzenadj")
    DMIDECODE = os.path.join(ASSETS_DIR, "Darwin", "dmidecode")
    CMD_FILE  = os.path.join(_ROOT, "UXTU4Unix.command")
else:
    RYZENADJ  = os.path.join(ASSETS_DIR, "Linux", "ryzenadj")
    DMIDECODE = "dmidecode"
    CMD_FILE  = os.path.join(_ROOT, "UXTU4Unix.py")

_cfg = ConfigParser()

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
REQUIRED: dict[str, list[str]] = {
    "User":     ["mode"],
    "Settings": ["time", "dynamicmode", "reapply", "applyonstart",
                 "softwareupdate", "debug"],
    "Info":     ["cpu", "signature", "voltage", "max speed", "current speed",
                 "core count", "core enabled", "thread count",
                 "architecture", "family", "type"],
}
if KERNEL == "Darwin":
    REQUIRED["Settings"].append("sip")