"""
config.py - Central configuration management for UXTU4Unix.
"""
import os
import sys
from configparser import ConfigParser

LOCAL_VERSION = "0.5.22"
LOCAL_BUILD = "5-universal-2May26-r3"
GITHUB_API_URL = "https://api.github.com/repos/HorizonUnix/UXTU4Unix/releases/latest"
LATEST_VER_URL = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest"

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ASSETS_DIR = os.path.join(_ROOT, "Assets")
CONFIG_PATH = os.path.join(ASSETS_DIR, "config.toml")
MODULES_DIR = os.path.join(ASSETS_DIR, "Modules")
PRESETS_DIR = os.path.join(ASSETS_DIR, "Presets")

KERNEL = os.uname().sysname

if KERNEL == "Darwin":
    RYZENADJ = os.path.join(ASSETS_DIR, "Darwin", "ryzenadj")
    DMIDECODE = os.path.join(ASSETS_DIR, "Darwin", "dmidecode")
    CMD_FILE = os.path.join(_ROOT, "UXTU4Unix.command")
else:
    RYZENADJ = os.path.join(ASSETS_DIR, "Linux", "ryzenadj")
    DMIDECODE = "dmidecode"
    CMD_FILE = os.path.realpath(sys.argv[0])

_cfg = ConfigParser()
_loaded_preset = ""

def set_loaded_preset(name):
    global _loaded_preset
    _loaded_preset = name


def get_loaded_preset():
    return _loaded_preset


def load():
    _cfg.read(CONFIG_PATH)
    return _cfg


def get(section, key, fallback=""):
    return _cfg.get(section, key, fallback=fallback)


def set(section, key, value):
    if not _cfg.has_section(section):
        _cfg.add_section(section)
    _cfg.set(section, key, value)


def save():
    with open(CONFIG_PATH, "w") as f:
        _cfg.write(f)


def ensure_sections(*sections):
    for s in sections:
        if not _cfg.has_section(s):
            _cfg.add_section(s)


def is_debug():
    return get("Settings", "Debug", "1") == "1"


def instance():
    return _cfg


REQUIRED = {
    "User": ["mode"],
    "Settings": ["time", "dynamicmode", "reapply", "applyonstart", "softwareupdate", "debug"],
    "Info": ["cpu", "signature", "architecture", "family", "type"],
}
if KERNEL == "Darwin":
    REQUIRED["Settings"].append("sip")
