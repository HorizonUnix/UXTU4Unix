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
from .hardware import RYZEN_FAMILY, run_cmd
from .secure_password import get_password
from .ui import clear, pause

_AC_TYPES = frozenset({"Mains", "USB", "USB_C", "USB_PD", "USB_PD_DRP", "USB_C_DRP"})


def _strip_cpu_name(raw):
    for word in ("AMD", "with", "Mobile", "Ryzen", "Radeon", "Graphics", "Vega", "Gfx"):
        raw = raw.replace(word, "")
    return raw


def _family_idx(name):
    try:
        return RYZEN_FAMILY.index(name)
    except ValueError:
        return -1


def _preset_module_name(cpu_type, family, cpu_model, raw_cpu):
    is_ryzen9 = "Ryzen 9" in raw_cpu
    if cpu_type == "Amd_Apu":
        if _family_idx(family) < _family_idx("Matisse"):
            if any(s in cpu_model for s in ("U", "e", "Ce")):
                return "AMDAPUPreMatisse_U_e_Ce"
            if "H" in cpu_model:
                return "AMDAPUPreMatisse_H"
            if "GE" in cpu_model:
                return "AMDAPUPreMatisse_GE"
            if "G" in cpu_model:
                return "AMDAPUPreMatisse_G"
            return "AMDCPU"
        else:
            if family in ("DragonRange", "FireRange"):
                return "AMDAPUDragonFireRange"
            if family == "StrixHalo":
                return "AMDAPUStrixHalo"
            if family == "Mendocino" and "U" in cpu_model:
                return "AMDAPUPreMatisse_U_e_Ce"
            if "U" in cpu_model or ("AI" in cpu_model and "HX" not in cpu_model):
                return "AMDAPUPostMatisse_U"
            if "HX" in cpu_model:
                return "AMDAPUPostMatisse_HX"
            if "HS" in cpu_model:
                return "AMDAPUPostMatisse_HS"
            if "H" in cpu_model:
                return "AMDAPUPostMatisse_H"
            if "GE" in cpu_model:
                return "AMDAPUPostMatisse_GE"
            if "G" in cpu_model:
                return "AMDAPUPostMatisse_G"
            return "AMDCPU"
    if cpu_type == "Amd_Desktop_Cpu":
        if _family_idx(family) < _family_idx("Raphael"):
            if "E" in cpu_model:
                return "AMDCPUPreRaphael_E"
            if "X3D" in cpu_model:
                return "AMDCPUPreRaphael_X3D"
            if "X" in cpu_model and is_ryzen9:
                return "AMDCPUPreRaphael_X9"
            if "X" in cpu_model:
                return "AMDCPUPreRaphael_X"
            return "AMDCPUPreRaphael"
        else:
            if "E" in cpu_model:
                return "AMDCPU_E"
            if "X3D" in cpu_model:
                return "AMDCPU_X3D"
            if "X" in cpu_model and is_ryzen9:
                return "AMDCPU_X9"
            return "AMDCPU"
    return "AMDCPU"


def get_presets():
    raw_cpu = cfg.get("Info", "CPU")
    family = cfg.get("Info", "Family")
    cpu_type = cfg.get("Info", "Type")
    cpu_model = _strip_cpu_name(raw_cpu)
    mod_name = _preset_module_name(cpu_type, family, cpu_model, raw_cpu)
    full_mod = f"Assets.Presets.{mod_name}"
    module = importlib.import_module(full_mod)
    cfg.set_loaded_preset(full_mod)
    return module.PRESETS


def _on_ac():
    ac_online = False
    found_ac = False
    battery_discharging = False
    try:
        for entry in os.listdir("/sys/class/power_supply"):
            base = f"/sys/class/power_supply/{entry}"
            try:
                ptype = open(f"{base}/type").read().strip()
            except OSError:
                continue
            if ptype in _AC_TYPES:
                found_ac = True
                try:
                    if open(f"{base}/online").read().strip() == "1":
                        ac_online = True
                except OSError:
                    pass
            elif ptype == "Battery":
                try:
                    if open(f"{base}/status").read().strip().lower() == "discharging":
                        battery_discharging = True
                except OSError:
                    pass
    except Exception:
        pass
    if found_ac:
        return ac_online
    return not battery_discharging


def _build_command(args, user_mode):
    payload = user_mode.split() if args == "Custom" else args.split()
    return ["sudo", "-S", cfg.RYZENADJ] + payload


def _run_ryzenadj(command, password):
    result = subprocess.run(command, input=password, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(result.stdout.decode())
    if cfg.is_debug() and result.stderr:
        print(result.stderr.decode())


def _wait_or_back(seconds):
    interactive = sys.stdin.isatty()
    for _ in range(seconds):
        time.sleep(1)
        if interactive and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            if sys.stdin.readline().strip().lower() == "b":
                return True
    return False


def apply_smu(args, user_mode, *, save_to_config=True):
    if cfg.get("Info", "Type") == "Intel":
        clear()
        print("Intel chipsets are not currently supported.")
        pause()
        return

    if save_to_config and user_mode == "Custom":
        cfg.set("User", "Mode", "Custom")
        cfg.set("User", "CustomArgs", args)
        cfg.save()

    sleep_secs = int(float(cfg.get("Settings", "Time", "3")))
    password = (get_password() or "").encode()
    dynamic = cfg.get("Settings", "DynamicMode", "0") == "1"
    reapply = cfg.get("Settings", "ReApply", "0") == "1"
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
                effective_args = get_presets().get(effective_mode, args)
            clear()
            cmd = _build_command(effective_args, effective_mode)
            print(f"Preset       : {effective_mode}")
            print(f"Dynamic mode : {'Enabled' if dynamic else 'Disabled'}")
            print(f"Auto reapply : Enabled - every {sleep_secs}s")
            print("Press B + Enter to go back")
            print("-" * 15 + " RyzenAdj Output " + "-" * 15)
            _run_ryzenadj(cmd, password)
            if _wait_or_back(sleep_secs):
                cfg.set("Settings", "ReApply", saved_reapply)
                return
    else:
        clear()
        cmd = _build_command(args, user_mode)
        print(f"Preset       : {user_mode}")
        print("Auto reapply : Disabled")
        print("-" * 15 + " RyzenAdj Output " + "-" * 15)
        _run_ryzenadj(cmd, password)
        pause()


def _load_saved():
    presets = get_presets()
    user_mode = cfg.get("User", "Mode")
    if user_mode == "Custom":
        apply_smu("Custom", cfg.get("User", "CustomArgs"))
    elif user_mode in presets:
        apply_smu(presets[user_mode], user_mode)
    else:
        print("Config is missing or invalid - resetting...")
        pause()
        from .setup import run_welcome
        run_welcome()


def _select_premade(presets):
    clear()
    print("Select a premade preset:\n")
    names = list(presets.keys())
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    try:
        n = int(input("\nOption: ").strip())
        if 1 <= n <= len(names):
            selected = names[n - 1]
            prev = cfg.get("Settings", "DynamicMode", "0")
            cfg.set("Settings", "DynamicMode", "0")
            apply_smu(presets[selected], selected)
            cfg.set("Settings", "DynamicMode", prev)
        else:
            print("Out of range.")
            pause()
    except ValueError:
        print("Invalid input.")
        pause()


def preset_menu():
    presets = get_presets()
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
            _select_premade(presets)
        case "d":
            prev_dyn = cfg.get("Settings", "DynamicMode", "0")
            prev_reapply = cfg.get("Settings", "ReApply", "0")
            cfg.set("Settings", "DynamicMode", "1")
            cfg.set("Settings", "ReApply", "1")
            apply_smu(presets.get("Balance", ""), "Balance")
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