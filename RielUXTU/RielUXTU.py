import subprocess
import sys
import time
import os
import urllib.request
from configparser import ConfigParser

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

def create_config() -> None:
    cfg: ConfigParser = ConfigParser()
    cfg.add_section('User')
    print("------ First time setup ------")
    print("Preset power plan")
    for i, mode in enumerate(PRESETS, start=1):
        print(f"{i}. {mode}")

    choice = input("Choose your preset power plan by pressing number: ")
    try:
        preset_number = int(choice)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        cfg.set('User', 'Mode', preset_name)
        with open('config.ini', 'w') as config_file:
            cfg.write(config_file)
    except ValueError:
        print("Invalid input. Please enter a number.")

def read_config() -> str:
    cfg: ConfigParser = ConfigParser()
    cfg.read('config.ini')
    return cfg.get('User', 'Mode', fallback='')

def check_config_integrity(conf: ConfigParser) -> None:
    config_path = 'config.ini'
    
    if not os.path.isfile(config_path) or os.stat(config_path).st_size == 0:
        create_config()
        return

    conf.read(config_path)
    
    if not conf.has_section('User'):
        create_config()

def get_latest_version():
    latest_version_url = "https://github.com/gorouflex/rieluxtu4mac/releases/latest"
    latest_version = urllib.request.urlopen(latest_version_url).geturl()
    return latest_version.split("/")[-1]

def check_for_updates():
    local_version = "0.0.4"
    latest_version = get_latest_version()

    if local_version < latest_version:
        print("A new update is available! Please visit the following link for details:")
        print("https://github.com/gorouflex/RielUXTU4Mac/releases/latest")
        sys.exit()
    elif local_version > latest_version:
        print("Welcome to RielUXTU4Mac Beta Program.")
        print("This build may not be as stable as expected. Only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            sys.exit()
        
def clear():
    _ = os.system('cls') if os.name == 'nt' else os.system('clear')

def run_command(args):
    command = ["sudo", "./ryzenadj"] + args.split()
    while True:
        subprocess.run(command)
        time.sleep(3)
        clear()
        print("Script will be reapplied every 3 seconds since RyzenAdj can easily reset just like UXTU")


check_for_updates()

config = ConfigParser()
check_config_integrity(config)
config.read('config.ini')

user_mode = read_config()

if user_mode:
    print(f"Using mode: {user_mode}")
    run_command(PRESETS[user_mode])
else:
    print("Config file is missing or invalid. Please run the script again.")
