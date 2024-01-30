import os
import sys
import time
import subprocess
import getpass
import urllib.request
from configparser import ConfigParser

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Balance": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=22000 --fast-limit=24000 --stapm-time=64 --slow-limit=22000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Performance": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Extreme": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=30000 --fast-limit=34000 --stapm-time=64 --slow-limit=32000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000"
}

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/gorouflex/rieluxtu4mac/releases/latest"
LOCAL_VERSION = "0.0.5"

def create_config() -> None:
    cfg = ConfigParser()
    cfg.add_section('User')
    print("------ First-time setup ------")
    print("Preset power plan")
    for i, mode in enumerate(PRESETS, start=1):
        print(f"{i}. {mode}")

    choice = input("Choose your preset power plan by pressing number: ")
    password = getpass.getpass("Enter your login password: ")
    try:
        preset_number = int(choice)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        cfg.set('User', 'Mode', preset_name)
        cfg.set('User', 'Password', password)
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    except ValueError:
        print("Invalid input. Please enter a number.")

def read_config() -> str:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.get('User', 'Mode', fallback='')

def check_config_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        create_config()
        return

    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    
    if not cfg.has_section('User'):
        create_config()

def get_latest_version():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def check_for_updates():
    latest_version = get_latest_version()

    if LOCAL_VERSION < latest_version:
        print("A new update is available! Please visit the following link for details:")
        print(LATEST_VERSION_URL)
        sys.exit()
    elif LOCAL_VERSION > latest_version:
        print("Welcome to RielUXTU4Mac Beta Program.")
        print("This build may not be as stable as expected. Only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            sys.exit()
        
def clear():
    _ = os.system('cls') if os.name == 'nt' else os.system('clear')

def run_command(args, user_mode):
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    command = ["sudo", "-S", "./ryzenadj"] + args.split()
    while True:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(password.encode())
        print(stdout.decode())  
        if stderr:
            print(f"Error: {stderr.decode()}")
        time.sleep(3)
        clear()
        print(f"Using mode: {user_mode}")
        print("Script will be reapplied every 3 seconds just like UXTU")

def main():
    check_for_updates()
    check_config_integrity()
    user_mode = read_config()

    if user_mode:
        print(f"Using mode: {user_mode}")
        run_command(PRESETS[user_mode], user_mode)
    else:
        print("Config file is missing or invalid. Please run the script again.")

if __name__ == "__main__":
    main()
