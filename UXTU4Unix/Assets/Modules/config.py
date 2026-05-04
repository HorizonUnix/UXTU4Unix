"""
config.py
"""
import os
import sys
from configparser import ConfigParser

LOCAL_VERSION = "0.6.0"
LOCAL_BUILD   = "b6-linux-4May26-Beta06"

GITHUB_API_URL = "https://api.github.com/repos/HorizonUnix/UXTU4Unix/releases/latest"
LATEST_VER_URL = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest"

_ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ASSETS_DIR  = os.path.join(_ROOT, "Assets")
CONFIG_PATH = os.path.join(ASSETS_DIR, "config.toml")
MODULES_DIR = os.path.join(ASSETS_DIR, "Modules")
PRESETS_DIR = os.path.join(ASSETS_DIR, "Presets")

RYZENADJ = os.path.join(ASSETS_DIR, "Linux", "ryzenadj")
CMD_FILE  = os.path.realpath(sys.argv[0])
DMIDECODE = "dmidecode"
KERNEL    = os.uname().sysname

VENV_DIR    = "/opt/uxtu4unix/venv"
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python3")

ZMQ_SOCKET_PATH = "/run/uxtu4unix.sock"
ZMQ_SOCKET_ADDR = f"ipc://{ZMQ_SOCKET_PATH}"

_cfg           = ConfigParser()
_loaded_preset = ""


def set_loaded_preset(name: str) -> None:
    global _loaded_preset
    _loaded_preset = name


def get_loaded_preset() -> str:
    return _loaded_preset


def load():
    _cfg.read(CONFIG_PATH)
    return _cfg


def get(section: str, key: str, fallback: str = "") -> str:
    return _cfg.get(section, key, fallback=fallback)


def set(section: str, key: str, value: str) -> None:
    if not _cfg.has_section(section):
        _cfg.add_section(section)
    _cfg.set(section, key, value)


def save() -> None:
    with open(CONFIG_PATH, "w") as f:
        _cfg.write(f)


def ensure_sections(*sections) -> None:
    for s in sections:
        if not _cfg.has_section(s):
            _cfg.add_section(s)


def is_debug() -> bool:
    return get("Settings", "Debug", "1") == "1"


def instance() -> ConfigParser:
    return _cfg


REQUIRED: dict[str, list[str]] = {
    "User":     ["mode"],
    "Settings": ["time", "dynamicmode", "reapply", "applyonstart", "softwareupdate", "debug"],
    "Info":     ["cpu", "signature", "architecture", "family", "type"],
}