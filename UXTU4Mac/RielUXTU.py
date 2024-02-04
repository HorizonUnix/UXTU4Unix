import os
import sys
import time
import subprocess
import getpass
import webbrowser
import urllib.request
from configparser import ConfigParser

PRESETS = {
    "Performance": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=30000  --fast-limit=34000 --stapm-time=64 --slow-limit=32000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Extreme": "--max-performance",
    "Auto": "--power-saving"
}

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.0.91"

def clr_print_logo():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
    ██╗   ██╗██╗  ██╗████████╗██╗   ██╗██╗  ██╗███╗   ███╗ █████╗  ██████╗
    ██║   ██║╚██╗██╔╝╚══██╔══╝██║   ██║██║  ██║████╗ ████║██╔══██╗██╔════╝
    ██║   ██║ ╚███╔╝    ██║   ██║   ██║███████║██╔████╔██║███████║██║
    ██║   ██║ ██╔██╗    ██║   ██║   ██║╚════██║██║╚██╔╝██║██╔══██║██║
    ╚██████╔╝██╔╝ ██╗   ██║   ╚██████╔╝     ██║██║ ╚═╝ ██║██║  ██║╚██████╗
     ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝      ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝
    Version: {}
    """.format(LOCAL_VERSION))

def main_menu():
    clr_print_logo()
    print("1. Apply preset")
    print("2. Settings")
    print()
    print("A. About")
    print()
    print("Q. Quit")

def about_menu():
    clr_print_logo()
    print()
    print("About UXTU4Mac")
    print()
    print("Latest version on GitHub: {}".format(get_latest_ver()))
    print("----------------------------")
    print("Main developer: GorouFlex")
    print("CLI: GorouFlex")
    print("GUI: NotchApple1703")
    print("----------------------------")
    print()
    print("1. Open GitHub")
    print("2. Change logs")
    print()
    print("B. Back")

def create_cfg() -> None:
    cfg = ConfigParser()
    cfg.add_section('User')
    clr_print_logo()
    print("------ Settings ------")
    print("Preset power plan")
    for i, mode in enumerate(PRESETS, start=1):
        print(f"{i}. {mode}")
    
    print()
    print("We recommend using Auto preset for normal tasks and better power management, and Extreme preset for unlocking full potential performance")
    choice = input("Choose your preset power plan by pressing a number followed by the preset: ")
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
        sys.exit(-1)

def read_cfg() -> str:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.get('User', 'Mode', fallback='')

def skip_welcome() -> bool:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.getboolean('User', 'SkipWelcome', fallback=False)

def check_cfg_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        create_cfg()
        return

    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    
    if not cfg.has_section('User'):
        create_cfg()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def check_updates():
    latest_version = get_latest_ver()

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

def run_cmd(args, user_mode):
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    command = ["sudo", "-S", "./ryzenadj"] + args.split()
    while True:
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
        if result.stderr:
            print(f"Error: {result.stderr.decode()}")
        time.sleep(3)
        clr_print_logo()
        print(f"Using mode: {user_mode}")
        print("Script will be reapplied every 3 seconds just like UXTU")
        print("------ RyzenAdj Log ------")

def info():
    while True:
        about_menu()
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
    webbrowser.open("https://www.github.com/AppleOSX/UXTU4Mac")

def open_releases():
    webbrowser.open("https://github.com/AppleOSX/UXTU4Mac/releases/tag/{}".format(get_latest_ver()))

def main():
    check_updates()
    check_cfg_integrity()
    user_mode = read_cfg()

    if not skip_welcome():
        while True:
            main_menu()
            choice = input("Option: ")

            if choice == "1":
                clr_print_logo()
                run_cmd(PRESETS[read_cfg()], read_cfg())
            elif choice == "2":
                clr_print_logo()
                create_cfg()
            elif choice.lower() == "a":
                info()
            elif choice.lower() == "q":
                sys.exit()
            else:
                print("Invalid choice. Please enter a valid option.")
    else:
        if user_mode:
            clr_print_logo()
            print(f"Using mode: {user_mode}")
            run_cmd(PRESETS[user_mode], user_mode)
        else:
            print("Config file is missing or invalid. Please run the script again.")

if __name__ == "__main__":
    main()
