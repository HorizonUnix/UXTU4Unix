"""
power.py
"""

from __future__ import annotations
import importlib
from . import config as cfg
from .hardware import RYZEN_FAMILY
from .ui import menu, clear, ask, pause


def _strip_cpu_name(raw: str) -> str:
    for word in ("AMD", "with", "Mobile", "Ryzen", "Radeon", "Graphics", "Vega", "Gfx"):
        raw = raw.replace(word, "")
    return raw


def _family_idx(name: str) -> int:
    try:
        return RYZEN_FAMILY.index(name)
    except ValueError:
        return -1


def _preset_module_name(cpu_type: str, family: str, cpu_model: str, raw_cpu: str) -> str:
    is_ryzen9 = "Ryzen 9" in raw_cpu

    if cpu_type == "Amd_Apu":
        if _family_idx(family) < _family_idx("Matisse"):
            if any(s in cpu_model for s in ("U", "e", "Ce")):
                return "AMDAPUPreMatisse_U_e_Ce"
            if "H" in cpu_model:   return "AMDAPUPreMatisse_H"
            if "GE" in cpu_model:  return "AMDAPUPreMatisse_GE"
            if "G" in cpu_model:   return "AMDAPUPreMatisse_G"
            return "AMDCPU"
        else:
            if family in ("DragonRange", "FireRange"): return "AMDAPUDragonFireRange"
            if family == "StrixHalo":                  return "AMDAPUStrixHalo"
            if family == "Mendocino" and "U" in cpu_model: return "AMDAPUPreMatisse_U_e_Ce"
            if "U" in cpu_model or ("AI" in cpu_model and "HX" not in cpu_model):
                return "AMDAPUPostMatisse_U"
            if "HX" in cpu_model:  return "AMDAPUPostMatisse_HX"
            if "HS" in cpu_model:  return "AMDAPUPostMatisse_HS"
            if "H" in cpu_model:   return "AMDAPUPostMatisse_H"
            if "GE" in cpu_model:  return "AMDAPUPostMatisse_GE"
            if "G" in cpu_model:   return "AMDAPUPostMatisse_G"
            return "AMDCPU"

    if cpu_type == "Amd_Desktop_Cpu":
        if _family_idx(family) < _family_idx("Raphael"):
            if "E"   in cpu_model: return "AMDCPUPreRaphael_E"
            if "X3D" in cpu_model: return "AMDCPUPreRaphael_X3D"
            if "X"   in cpu_model and is_ryzen9: return "AMDCPUPreRaphael_X9"
            if "X"   in cpu_model: return "AMDCPUPreRaphael_X"
            return "AMDCPUPreRaphael"
        else:
            if "E"   in cpu_model: return "AMDCPU_E"
            if "X3D" in cpu_model: return "AMDCPU_X3D"
            if "X"   in cpu_model and is_ryzen9: return "AMDCPU_X9"
            return "AMDCPU"

    return "AMDCPU"


def get_presets() -> dict:
    raw_cpu   = cfg.get("Info", "CPU")
    family    = cfg.get("Info", "Family")
    cpu_type  = cfg.get("Info", "Type")
    cpu_model = _strip_cpu_name(raw_cpu)
    mod_name  = _preset_module_name(cpu_type, family, cpu_model, raw_cpu)
    full_mod  = f"Assets.Presets.{mod_name}"
    module    = importlib.import_module(full_mod)
    cfg.set_loaded_preset(full_mod)
    return module.PRESETS


def apply_smu(args: str, user_mode: str, *, save_to_config: bool = True) -> None:
    from .ipc import get_client

    if cfg.get("Info", "Type") == "Intel":
        clear()
        print("  Intel chipsets are not supported.")
        pause()
        return

    if save_to_config and user_mode != "Custom":
        cfg.set("User", "Mode", user_mode)
        cfg.save()
    elif save_to_config and user_mode == "Custom":
        cfg.set("User", "Mode", "Custom")
        cfg.set("User", "CustomArgs", args)
        cfg.save()

    client = get_client()
    if not client.ping():
        clear()
        print("  Daemon is not running.")
        print("  sudo systemctl enable --now uxtu4unix.service")
        pause()
        return

    interval = int(float(cfg.get("Settings", "Time", "3")))
    dynamic  = cfg.get("Settings", "DynamicMode", "0") == "1"
    reapply  = cfg.get("Settings", "ReApply", "0") == "1" or dynamic

    if reapply:
        client.apply_loop(args=args, mode=user_mode, interval=interval, dynamic=dynamic)
    else:
        client.apply(args=args, mode=user_mode)


def _daemon_status_screen() -> None:
    from .ipc import get_client
    clear()
    client = get_client()
    if not client.ping():
        print("  Daemon is not running.")
        print("  sudo systemctl enable --now uxtu4unix.service")
    else:
        s = client.status()
        print(f"  Auto reapply : {'ON' if s.get('running_loop') else 'OFF'}")
        print(f"  Mode         : {'Dynamic' if s.get('dynamic') else s.get('mode', 'N/A')}")
        print(f"  Interval     : {s.get('interval', '?')}s")
        print(f"  Power        : {'AC' if s.get('on_ac') else 'Battery'}")
        last = s.get("last_output", "")
        if last:
            print(f"\n  {'─'*30}\n")
            for line in last[:500].splitlines():
                print(f"  {line}")
    pause()


def _stop_loop_screen() -> None:
    from .ipc import get_client
    client = get_client()
    if client.ping():
        client.stop_loop()
        cfg.set("Settings", "ReApply", "0")
        cfg.save()


def _start_loop_screen() -> None:
    from .ipc import get_client
    cfg.set("Settings", "ReApply", "1")
    cfg.save()
    client = get_client()
    if client.ping():
        client.apply_saved()


def _reapply_interval_menu() -> None:
    clear()
    current = cfg.get("Settings", "Time", "3")
    val = ask("Reapply interval in seconds", default=current)
    if val.isdigit():
        cfg.set("Settings", "Time", val)
        cfg.save()
        from .ipc import get_client
        client = get_client()
        if client.ping():
            client.apply_saved()
    else:
        print("\n  Must be a whole number.")
        pause()


def _toggle_dynamic_item(idx: int, items: list) -> None:
    on = cfg.get("Settings", "DynamicMode", "0") == "1"
    cfg.set("Settings", "DynamicMode", "0" if on else "1")
    cfg.save()
    items[idx] = ("Dynamic mode", "OFF" if on else "ON", "toggle")

    new_mode = cfg.get("User", "Mode") if on else "Dynamic"
    items[0] = ("Select preset", new_mode)

    if not on:
        cfg.set("Settings", "ReApply", "1")
        cfg.save()
        interval = cfg.get("Settings", "Time", "3")
        for i, item in enumerate(items):
            lbl = item[0] if isinstance(item, (tuple, list)) else item
            if lbl == "Start reapply":
                items[i] = ("Stop reapply", "[dynamic]", "disabled")
                items.insert(i + 1, ("Reapply interval", f"{interval}s"))
                break
            elif lbl == "Stop reapply":
                items[i] = ("Stop reapply", "[dynamic]", "disabled")
                break
    else:
        loop = cfg.get("Settings", "ReApply", "0") == "1"
        for i, item in enumerate(items):
            lbl = item[0] if isinstance(item, (tuple, list)) else item
            if lbl == "Stop reapply":
                if loop:
                    items[i] = ("Stop reapply", "")
                else:
                    items[i] = ("Start reapply", "")
                    if i + 1 < len(items) and items[i + 1][0] == "Reapply interval":
                        items.pop(i + 1)
                break

    from .ipc import get_client
    client = get_client()
    if not client.ping():
        return

    if on:
        client.apply_saved()
    else:
        presets = get_presets()
        apply_smu(presets.get("Balance", ""), "Balance", save_to_config=False)


def preset_menu() -> None:
    presets  = get_presets()
    names    = list(presets.keys())
    last_idx = 0

    while True:
        dynamic  = cfg.get("Settings", "DynamicMode", "0") == "1"
        interval = cfg.get("Settings", "Time", "3")
        try:
            from .ipc import get_client
            s    = get_client().status()
            mode = "Dynamic" if dynamic else (s.get("mode") or cfg.get("User", "Mode"))
            loop = s.get("running_loop", False)
        except Exception:
            mode = "Dynamic" if dynamic else cfg.get("User", "Mode")
            loop = cfg.get("Settings", "ReApply", "0") == "1"

        items: list = [
            ("Select preset",    mode),
            ("Dynamic mode",     "ON" if dynamic else "OFF", "toggle"),
            ("Custom arguments", ""),
            ("─", "", "sep"),
        ]
        if loop:
            stop_row = ("Stop reapply", "[dynamic]", "disabled") if dynamic else ("Stop reapply", "")
            items.append(stop_row)
            items.append(("Reapply interval", f"{interval}s"))
        else:
            items.append(("Start reapply", ""))
        items += [
            ("Daemon status", ""),
            ("Back",          ""),
        ]

        choice = menu(
            "Power Management", items,
            selected=min(last_idx, len(items) - 1),
            on_toggle=_toggle_dynamic_item,
        )
        if choice == -1:
            return

        last_idx = choice
        lbl = items[choice][0]
        tag = items[choice][2] if len(items[choice]) > 2 else ""

        if lbl == "Back":
            return
        elif lbl == "Select preset":
            _select_preset_menu(presets, names, mode)
        elif lbl == "Dynamic mode":
            _toggle_dynamic_item(choice, items)
        elif lbl == "Custom arguments":
            _custom_args_menu()
        elif lbl == "Reapply interval":
            _reapply_interval_menu()
        elif lbl == "Stop reapply" and tag != "disabled":
            _stop_loop_screen()
        elif lbl == "Start reapply":
            _start_loop_screen()
        elif lbl == "Daemon status":
            _daemon_status_screen()


def _select_preset_menu(presets: dict, names: list, current: str) -> None:
    items = [(n, "← current" if n == current else "") for n in names] + [("Back", "")]
    choice = menu("Select Preset", items)
    if choice == -1 or items[choice][0] == "Back":
        return
    selected = names[choice]
    cfg.set("User",     "Mode",        selected)
    cfg.set("Settings", "DynamicMode", "0")
    cfg.save()
    apply_smu(presets[selected], selected, save_to_config=False)


def _custom_args_menu() -> None:
    clear()
    args = ask("ryzenadj arguments")
    if args:
        cfg.set("Settings", "DynamicMode", "0")
        cfg.save()
        apply_smu(args, "Custom", save_to_config=True)


def _daemon_apply_saved() -> None:
    try:
        from .ipc import get_client
        client = get_client()
        if client.ping():
            client.apply_saved()
    except Exception:
        pass