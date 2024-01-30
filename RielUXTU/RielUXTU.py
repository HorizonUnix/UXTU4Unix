import subprocess
import sys
import time

PRESETS = {
    "Eco": (
        "--tctl-temp=95 "
        "--apu-skin-temp=45 "
        "--stapm-limit=6000 "
        "--fast-limit=8000 "
        "--stapm-time=64 "
        "--slow-limit=6000 "
        "--slow-time=128 "
        "--vrm-current=180000 "
        "--vrmmax-current=180000 "
        "--vrmsoc-current=180000 "
        "--vrmsocmax-current=180000 "
        "--vrmgfx-current=180000"
    ),
    "Balance": (
        "--tctl-temp=95 "
        "--apu-skin-temp=45 "
        "--stapm-limit=22000 "
        "--fast-limit=24000 "
        "--stapm-time=64 "
        "--slow-limit=22000 "
        "--slow-time=128 "
        "--vrm-current=180000 "
        "--vrmmax-current=180000 "
        "--vrmsoc-current=180000 "
        "--vrmsocmax-current=180000 "
        "--vrmgfx-current=180000"
    ),
    "Performance": (
        "--tctl-temp=95 "
        "--apu-skin-temp=45 "
        "--stapm-limit=6000 "
        "--fast-limit=8000 "
        "--stapm-time=64 "
        "--slow-limit=6000 "
        "--slow-time=128 "
        "--vrm-current=180000 "
        "--vrmmax-current=180000 "
        "--vrmsoc-current=180000 "
        "--vrmsocmax-current=180000 "
        "--vrmgfx-current=180000"
    ),
    "Extreme": (
        "--tctl-temp=95 "
        "--apu-skin-temp=95 "
        "--stapm-limit=30000 "
        "--fast-limit=34000 "
        "--stapm-time=64 "
        "--slow-limit=32000 "
        "--slow-time=128 "
        "--vrm-current=180000 "
        "--vrmmax-current=180000 "
        "--vrmsoc-current=180000 "
        "--vrmsocmax-current=180000 "
        "--vrmgfx-current=180000"
    )
}

def run_command(args):
    command = ["sudo", "./ryzenadj"] + args.split()
    while True:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        if result.returncode != 255:
            print("Applied preset failed!")
            print(result.returncode)
        time.sleep(3)


if len(sys.argv) > 1:
    user_input = sys.argv[1]
    try:
        preset_number = int(user_input)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        run_command(PRESETS[preset_name])
    except ValueError:
        run_command(user_input)
else:
    print("Current Preset:")
    for i, preset in enumerate(PRESETS, start=1):
        print(f"{i}. {preset}")
    user_input = input("Choose a preset by enter number or enter custom arguments: ")
    print("Script will reapplied every 3 seconds since RyzenAdj can easily reset just like UXTU")

    try:
        preset_number = int(user_input)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        run_command(PRESETS[preset_name])
    except ValueError:
        run_command(user_input)
