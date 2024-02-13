import os
import sys
import time
import subprocess
import getpass
import webbrowser
import logging
import urllib.request
from configparser import ConfigParser

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Performance": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=28000 --fast-limit=28000 --stapm-time=64 --slow-limit=28000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000 ",
    "Extreme": "--max-performance",
    "Auto": "--power-saving"
}

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.0.95"

if not os.path.exists('Logs'):
    os.mkdir('Logs')

logging.basicConfig(filename='Logs/UXTU4Mac.log', filemode='w', encoding='utf-8',
                    level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logging.getLogger().addHandler(console_handler)

def get_system_info(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8').strip()

def print_system_info():
    logging.info("Device Information:")
    logging.info(f'  Name: {get_system_info("scutil --get ComputerName")}')
    logging.info(f'  Model: {get_system_info("sysctl -n hw.model")}')
    logging.info(f'  macOS version: {get_system_info("sysctl -n kern.osrelease")}')

    logging.info("\nProcessor Information:")
    logging.info(
        f'  Processor: {get_system_info("sysctl -n machdep.cpu.brand_string")}'
    )
    logging.info(f'  Cores: {get_system_info("sysctl -n hw.physicalcpu")}')
    logging.info(f'  Threads: {get_system_info("sysctl -n hw.logicalcpu")}')
    base_clock = float(get_system_info("sysctl -n hw.cpufrequency_max")) / (10**9)
    logging.info("  Base clock: {:.2f} GHz".format(base_clock))
    logging.info(
        f'  Features: {get_system_info("sysctl -a | grep machdep.cpu.features").split(": ")[1]}'
    )
    logging.info(f'  Vendor: {get_system_info("sysctl -n machdep.cpu.vendor")}')
    logging.info(f'  Family: {get_system_info("sysctl -n machdep.cpu.family")}')

    logging.info("\nMemory Information:")
    memory = float(get_system_info("sysctl -n hw.memsize")) / (1024**3)
    logging.info("  Memory: {:.2f} GB".format(memory))
    if has_battery := get_system_info(
        "system_profiler SPPowerDataType | grep 'Battery Information'"
    ):
        logging.info("\nBattery Information:")
        logging.info("  Health: {}".format(get_system_info("pmset -g batt | egrep '([0-9]+\\%).*' -o --colour=auto | cut -f1 -d';'")))
        logging.info("  Cycles: {}".format(get_system_info("system_profiler SPPowerDataType | grep 'Cycle Count' | awk '{print $3}'")))
        logging.info("  Capacity: {}".format(get_system_info("system_profiler SPPowerDataType | grep 'Full Charge Capacity' | awk '{print $5}'")))

def print_hardware_info():
    clr_print_logo()
    print_system_info()
    input("Press Enter to go back to the main menu...")
    
def clr_print_logo():
    os.system('cls' if os.name == 'nt' else 'clear')
    logging.info("""
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
    logging.info("1. Apply preset")
    logging.info("2. Settings")
    logging.info("")
    logging.info("H. Hardware Information")
    logging.info("A. About")
    logging.info("Q. Quit")

def about_menu():
    clr_print_logo()
    logging.info("")
    logging.info("About UXTU4Mac")
    logging.info("")
    logging.info(f"Latest version on GitHub: {get_latest_ver()}")
    logging.info("----------------------------")
    logging.info("Main developer: GorouFlex")
    logging.info("CLI: GorouFlex")
    logging.info("GUI: NotchApple1703")
    logging.info("----------------------------")
    logging.info("")
    logging.info("1. Open GitHub")
    logging.info("2. Change logs")
    logging.info("")
    logging.info("B. Back")

def create_cfg() -> None:
    cfg = ConfigParser()
    cfg.add_section('User')
    clr_print_logo()
    logging.info("------ Settings ------")
    logging.info("Preset power plan")
    for i, mode in enumerate(PRESETS, start=1):
        logging.info(f"{i}. {mode}")
    
    logging.info("")
    logging.info("We recommend using Auto preset for normal tasks and better power management,\nand Extreme preset for unlocking full potential performance")
    choice = input("Choose your preset by pressing a number followed by the preset (1,2,3,4): ")
    password = getpass.getpass("Enter your login password: ")
    skip_welcome = input("Do you want to skip the welcome menu? (y/n): ").lower()
    start_with_macos = input("Do you want this script to start with macOS? (Login Items) (y/n): ").lower()
    
    if start_with_macos == 'y':
        current_dir = os.path.dirname(os.path.realpath(__file__))
        command_file = os.path.join(current_dir, 'UXTU4Mac.command')
        command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
        subprocess.call(command, shell=True)
        
    try:
        preset_number = int(choice)
        preset_name = list(PRESETS.keys())[preset_number - 1]
        cfg.set('User', 'Mode', preset_name)
        cfg.set('User', 'Password', password)
        cfg.set('User', 'SkipWelcome', '1' if skip_welcome == 'y' else '0')
        cfg.set('User', 'SkipCFU', '0')
                
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    except ValueError:
        logging.info("Invalid input. Please enter a number.")
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
        clr_print_logo()
        logging.info("A new update is available! Please visit the following link for details:")
        logging.info(LATEST_VERSION_URL)
        sys.exit()
    elif LOCAL_VERSION > latest_version:
        clr_print_logo()
        logging.info("Welcome to RielUXTU4Mac Beta Program.")
        logging.info("This build may not be as stable as expected. Only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            sys.exit()

def run_cmd(args, user_mode):
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    command = ["sudo", "-S", "Assets/ryzenadj"] + args.split()
    while True:
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.info(f"Error: {result.stderr.decode()}")
        time.sleep(3)
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        logging.info("Script will be reapplied every 3 seconds just like UXTU")
        logging.info("------ RyzenAdj Log ------")

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
            logging.info("Invalid choice. Please enter a valid option.")

def open_github():
    webbrowser.open("https://www.github.com/AppleOSX/UXTU4Mac")

def open_releases():
    webbrowser.open(
        f"https://github.com/AppleOSX/UXTU4Mac/releases/tag/{get_latest_ver()}"
    )

def main():
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    if cfg.get('User', 'skipcfu', fallback = '0') == '0':
       try:
         check_updates()
       except:
         clr_print_logo()
         logging.info("No internet connection, failed to fetch update. Try again")
         sys.exit()
        
    check_cfg_integrity()
    user_mode = read_cfg()

    if not skip_welcome():
        while True:
            main_menu()
            choice = input("Option: ")
            if choice == "1":
                clr_print_logo()
                logging.info("Apply Preset:")
                logging.info("1. Load from config file")
                logging.info("2. Custom preset")
                logging.info("")
                logging.info("B. Back")
                preset_choice = input("Option: ")

                if preset_choice == "1":
                    if user_mode := read_cfg():
                        clr_print_logo()
                        logging.info(f"Using mode: {user_mode}")
                        run_cmd(PRESETS[user_mode], user_mode)
                    else:
                        logging.info("Config file is missing or invalid. Please run the script again.")
                elif preset_choice == "2":
                    custom_args = input("Custom arguments (preset): ")
                    clr_print_logo()
                    user_mode = "Custom"
                    logging.info(f"Using mode: {user_mode}")
                    run_cmd(custom_args, user_mode)
                elif preset_choice.lower() == "b":
                      continue
                else:
                    logging.info("Invalid choice. Please enter a valid option.")
            elif choice == "2":
                clr_print_logo()
                create_cfg()
            elif choice.lower() == "h":
                print_hardware_info()
            elif choice.lower() == "a":
                info()
            elif choice.lower() == "q":
                sys.exit()
            else:
                logging.info("Invalid choice. Please enter a valid option.")
    elif user_mode:
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        run_cmd(PRESETS[user_mode], user_mode)
    else:
        logging.info("Config file is missing or invalid. Please run the script again.")

if __name__ == "__main__":
    main()
