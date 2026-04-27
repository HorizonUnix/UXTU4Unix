"""
power.py - Preset resolution and RyzenAdj power management.
"""

import importlib
import os
import select
import subprocess
import sys
import time

from . import config as cfg
from .hardware import RYZEN_FAMILY, check_nvram, run_cmd
from .secure_password import get_password
from .ui import clear, pause

# Preset

def _strip_cpu_name(raw: str) -> str:
    """Remove common marketing words from a CPU name string."""
    noise = ("AMD", "with", "Mobile", "Ryzen", "Radeon",
             "Graphics", "Vega", "Gfx")
    for word in noise:
        raw = raw.replace(word, "")
    return raw


def _preset_module_name(cpu_type: str, family: str, cpu_model: str, raw_cpu: str) -> str:
    """Return the Presets sub-module name for this CPU configuration."""

    is_ryzen9 = "Ryzen 9" in raw_cpu

    def family_idx(name: str) -> int:
        try:
            return RYZEN_FAMILY.index(name)
        except ValueError:
            return -1

    if cpu_type == "Amd_Apu":
        if family_idx(family) < family_idx("Matisse"):
            # Pre-Matisse APU
            if any(s in cpu_model for s in ("U", "e", "Ce")):
                return "AMDAPUPreMatisse_U_e_Ce"
            if "H" in cpu_model:   return "AMDAPUPreMatisse_H"
            if "GE" in cpu_model:  return "AMDAPUPreMatisse_GE"
            if "G" in cpu_model:   return "AMDAPUPreMatisse_G"
            return "AMDCPU"
        else:
            # Post-Matisse APU
            if family in ("DragonRange", "FireRange"):
                return "AMDAPUDragonFireRange"
            if family == "StrixHalo":
                return "AMDAPUStrixHalo"
            if family == "Mendocino" and "U" in cpu_model:
                return "AMDAPUPreMatisse_U_e_Ce"
            if "U" in cpu_model or ("AI" in cpu_model and "HX" not in cpu_model):
                return "AMDAPUPostMatisse_U"
            if "HX" in cpu_model:  return "AMDAPUPostMatisse_HX"
            if "HS" in cpu_model:  return "AMDAPUPostMatisse_HS"
            if "H" in cpu_model:   return "AMDAPUPostMatisse_H"
            if "GE" in cpu_model:  return "AMDAPUPostMatisse_GE"
            if "G" in cpu_model:   return "AMDAPUPostMatisse_G"
            return "AMDCPU"

    if cpu_type == "Amd_Desktop_Cpu":
        pre_raphael = family_idx(family) < family_idx("Raphael")
        if pre_raphael:
            if "E"   in cpu_model:  return "AMDCPUPreRaphael_E"
            if "X3D" in cpu_model:  return "AMDCPUPreRaphael_X3D"
            if "X"   in cpu_model and is_ryzen9: return "AMDCPUPreRaphael_X9"
            if "X"   in cpu_model:  return "AMDCPUPreRaphael_X"
            return "AMDCPUPreRaphael"
        else:
            if "E"   in cpu_model:  return "AMDCPU_E"
            if "X3D" in cpu_model:  return "AMDCPU_X3D"
            if "X"   in cpu_model and is_ryzen9: return "AMDCPU_X9"
            return "AMDCPU"

    return "AMDCPU"


def get_presets() -> dict[str, str]:
    """
    Dynamically import the correct preset module and return its PRESETS dict.
    Also persists the chosen module name to config.
    """
    raw_cpu   = cfg.get("Info", "CPU")
    family    = cfg.get("Info", "Family")
    cpu_type  = cfg.get("Info", "Type")
    cpu_model = _strip_cpu_name(raw_cpu)

    mod_name = _preset_module_name(cpu_type, family, cpu_model, raw_cpu)
    full_mod = f"Assets.Presets.{mod_name}"

    module = importlib.import_module(full_mod)
    cfg.set("User", "Preset", full_mod)
    cfg.save()
    return module.PRESETS   # type: ignore[attr-defined]


_AC_TYPES = frozenset({
    "Mains", "USB", "USB_C", "USB_PD", "USB_PD_DRP", "USB_C_DRP",
})


def _on_ac() -> bool:
    """
    Return True when running on AC power (or unknown / desktop).
    """
    if cfg.KERNEL == "Darwin":
        out = subprocess.check_output(["pmset", "-g", "batt"]).decode()
        return "Battery Power" not in out

    ac_online           = False
    found_ac_supply     = False
    battery_discharging = False

    try:
        psu_root = "/sys/class/power_supply"
        for entry in os.listdir(psu_root):
            base = f"{psu_root}/{entry}"
            try:
                ptype = open(f"{base}/type").read().strip()
            except OSError:
                continue

            if ptype in _AC_TYPES:
                found_ac_supply = True
                try:
                    if open(f"{base}/online").read().strip() == "1":
                        ac_online = True
                except OSError:
                    pass

            elif ptype == "Battery":
                try:
                    status = open(f"{base}/status").read().strip().lower()
                    if status == "discharging":
                        battery_discharging = True
                except OSError:
                    pass

    except Exception:
        pass

    if found_ac_supply:
        return ac_online

    return not battery_discharging


# RyzenAdj invocation

def _build_command(args: str, user_mode: str) -> list[str]:
    """Build the sudo + ryzenadj command list."""
    payload = user_mode.split() if args == "Custom" else args.split()
    return ["sudo", "-S", cfg.RYZENADJ] + payload


def _run_ryzenadj(command: list[str], password: bytes) -> None:
    """Execute ryzenadj and print its output."""
    result = subprocess.run(
        command,
        input=password,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(result.stdout.decode())
    if cfg.is_debug() and result.stderr:
        print(result.stderr.decode())


def _wait_or_back(seconds: int) -> bool:
    """
    Sleep for *seconds* in 1-second increments, returning True if the user
    pressed 'b' + Enter to go back.
    """
    for _ in range(seconds):
        time.sleep(1)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            if sys.stdin.readline().strip().lower() == "b":
                return True
    return False


# Apply function

def apply_smu(args: str, user_mode: str, *, save_to_config: bool = True) -> None:
    """
    Apply power settings via ryzenadj.

    args        - ryzenadj argument string, or 'Custom'
    user_mode   - display name / custom args string (for Custom mode)
    save_to_config - persist mode to config.toml
    """
    cpu_type = cfg.get("Info", "Type")
    if cpu_type == "Intel":
        clear()
        print("Intel chipsets are not currently supported.")
        pause()
        return

    if cfg.KERNEL == "Darwin" and not check_nvram():
        clear()
        print(
            "Cannot run RyzenAdj.\n"
            "Missing: debug=0x144 boot-arg or required SIP flags.\n"
            "Go to Settings -> Install UXTU4Unix dependencies, then restart."
        )
        pause()
        return

    if save_to_config and user_mode == "Custom":
        cfg.set("User", "Mode", "Custom")
        cfg.set("User", "CustomArgs", args)
        cfg.save()

    sleep_secs    = int(float(cfg.get("Settings", "Time", "30")))
    password      = (get_password() or "").encode()
    dynamic       = cfg.get("Settings", "DynamicMode", "0") == "1"
    reapply       = cfg.get("Settings", "ReApply", "0") == "1"
    saved_reapply = cfg.get("Settings", "ReApply", "0")

    if dynamic:
        cfg.set("Settings", "ReApply", "1")
        reapply = True

    if reapply:
        while True:
            effective_mode = user_mode
            effective_args = args
            if dynamic:
                effective_mode = "Extreme" if _on_ac() else "Eco"
                dynamic_presets = get_presets()
                effective_args = dynamic_presets.get(effective_mode, args)

            clear()
            cmd = _build_command(effective_args, effective_mode)
            print(f"Preset        : {effective_mode}")
            print(f"Dynamic mode  : {'Enabled' if dynamic else 'Disabled'}")
            print("Auto reapply  : Enabled")
            print(f"Reapplying every {sleep_secs}s  -  press B + Enter to go back")
            print("-" * 44)
            _run_ryzenadj(cmd, password)

            if _wait_or_back(sleep_secs):
                cfg.set("Settings", "ReApply", saved_reapply)
                return
    else:
        clear()
        cmd = _build_command(args, user_mode)
        print(f"Preset        : {user_mode}")
        print("Auto reapply  : Disabled")
        print("-" * 44)
        _run_ryzenadj(cmd, password)
        pause()


# Preset menu
def _load_saved() -> None:
    """Load and apply the mode stored in config.toml."""
    PRESETS   = get_presets()
    user_mode = cfg.get("User", "Mode")
    if user_mode == "Custom":
        custom_args = cfg.get("User", "CustomArgs")
        apply_smu("Custom", custom_args)
    elif user_mode in PRESETS:
        apply_smu(PRESETS[user_mode], user_mode)
    else:
        print("Config is missing or invalid - resetting...")
        pause()
        from .setup import run_welcome
        run_welcome()


def _select_premade(PRESETS: dict[str, str]) -> None:
    """Sub-menu: pick a preset from the numbered list."""
    clear()
    print("Select a premade preset:\n")
    names = list(PRESETS.keys())
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    try:
        n = int(input("\nOption: ").strip())
        if 1 <= n <= len(names):
            selected = names[n - 1]
            prev_dynamic = cfg.get("Settings", "DynamicMode", "0")
            cfg.set("Settings", "DynamicMode", "0")
            apply_smu(PRESETS[selected], selected)
            cfg.set("Settings", "DynamicMode", prev_dynamic)
        else:
            print("Out of range.")
            pause()
    except ValueError:
        print("Invalid input.")
        pause()


def preset_menu() -> None:
    """Top-level 'Apply power management' menu."""
    PRESETS = get_presets()
    clear()
    print("Apply power management settings:\n")
    print("  1. Load from config file (saved preset)")
    print("  2. Load from premade preset list")
    print("\n  D. Dynamic Mode")
    print("  C. Custom arguments")
    print("  B. Back\n")
    choice = input("Option: ").strip().lower()

    match choice:
        case "1":
            _load_saved()
        case "2":
            _select_premade(PRESETS)
        case "d":
            prev_dyn     = cfg.get("Settings", "DynamicMode", "0")
            prev_reapply = cfg.get("Settings", "ReApply", "0")
            cfg.set("Settings", "DynamicMode", "1")
            cfg.set("Settings", "ReApply", "1")
            apply_smu(PRESETS.get("Balance", ""), "Balance")
            cfg.set("Settings", "DynamicMode", prev_dyn)
            cfg.set("Settings", "ReApply", prev_reapply)
        case "c":
            prev_dyn = cfg.get("Settings", "DynamicMode", "0")
            cfg.set("Settings", "DynamicMode", "0")
            custom_args = input("Enter your custom ryzenadj arguments: ")
            apply_smu("Custom", custom_args, save_to_config=False)
            cfg.set("Settings", "DynamicMode", prev_dyn)
        case "b":
            return
        case _:
            print("Invalid option.")
            pause()