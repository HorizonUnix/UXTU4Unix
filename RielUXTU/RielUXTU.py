import os
import sys
import time
import subprocess
import getpass
import webbrowser
import urllib.request
from configparser import ConfigParser

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Balance": "--power-saving",
    "Performance": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Extreme": "--max-performance"
}

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/gorouflex/rieluxtu4mac/releases/latest"
LOCAL_VERSION = "0.0.6"

def print_logo():
    print(r"""
  _____  _      _ _    ___   _________ _    _ _  _   __  __            
 |  __ \(_)    | | |  | \ \ / /__   __| |  | | || | |  \/  |           
 | |__) |_  ___| | |  | |\ V /   | |  | |  | | || |_| \  / | __ _  ___ 
 |  _  /| |/ _ \ | |  | | > <    | |  | |  | |__   _| |\/| |/ _` |/ __|
 | | \ \| |  __/ | |__| |/ . \   | |  | |__| |  | | | |  | | (_| | (__ 
 |_|  \_\_|\___|_|\____//_/ \_\  |_|   \____/   |_| |_|  |_|\__,_|\___|                                                                                                                                                                                   
Version 0.0.6 Stable - CLI Mode""")

def print_main_menu():
    clear()
    print_logo()
    print("1. Apply preset")
    print("2. Settings")
    print()
    print("A. About")
    print()
    print("Q. Quit")

def print_about_menu():
    clear()
    print_logo()
    print()
    print("About RielUXTU4Mac")
    print()
    print("Main developer: GorouFlex")
    print("GUI developer: NotchApple1703")
    print("CLI: GorouFlex")
    print(f"Latest version on GitHub: {get_latest_version()}")
    print()
    print("1. Open GitHub")
    print("2. Change logs")
    print()
    print("B. Back")

def create_config() -> None:
    cfg = ConfigParser()
    cfg.add_section('User')
    print("------ First-time setup ------")
    print("Preset power plan")
    for i, mode in enumerate(PRESETS, start=1):
        print(f"{i}. {mode}")

    choice = input("Choose your preset power plan by pressing number: ")
    password = getpass.getpass("Enter your login password: ")
    skip_welcome = input("Do you want to skip the welcome menu? (y/n): ").lower()

    try:
        preset_number = int(choice)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        cfg.set('User', 'Mode', preset_name)
        cfg.set('User', 'Password', password)
        cfg.set('User', 'SkipWelcome', '1' if skip_welcome == 'y' else '0')

        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    except ValueError:
        print("Invalid input. Please enter a number.")

def read_config() -> str:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.get('User', 'Mode', fallback='')

def check_skip_welcome() -> bool:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.get('User', 'SkipWelcome', fallback='0') == '1'

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
        print_logo()
        print(f"Using mode: {user_mode}")
        print("Script will be reapplied every 3 seconds just like UXTU")
        print("------ RyzenAdj Log ------")

def info():
    while True:
        print_about_menu()
        choice = input("Option: ")
        if choice == "1":
            open_github()
        elif choice == "2":
            open_releases()
        elif choice.lower() == "b":
            break
        else:
            print("Invalid choice. Please enter a valid option.")

def open_github():
    webbrowser.open("https://www.github.com/gorouflex/RielUXTU4Mac")

def open_releases():
    webbrowser.open(f"https://github.com/gorouflex/RielUXTU4Mac/releases/tag/{get_latest_version()}")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    check_for_updates()
    check_config_integrity()
    user_mode = read_config()

    if not check_skip_welcome():
        while True:
            print_main_menu()
            choice = input("Enter your choice: ")

            if choice == "1":
                clear()
                run_command(PRESETS[user_mode], user_mode)
            elif choice == "2":
                clear()
                create_config()
            elif choice.lower() == "a":
                info()
            elif choice.lower() == "q":
                sys.exit()
            else:
                print("Invalid choice. Please enter a valid option.")
    else:
        if user_mode:
            print(f"Using mode: {user_mode}")
            run_command(PRESETS[user_mode], user_mode)
        else:
            print("Config file is missing or invalid. Please run the script again.")

if __name__ == "__main__":
    main()
