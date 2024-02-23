import os
import sys
import time
import subprocess
import getpass
import webbrowser
import logging
import urllib.request
import plistlib
import threading
import base64
from configparser import ConfigParser

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.0.99"

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Performance": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=28000 --fast-limit=28000 --stapm-time=64 --slow-limit=28000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000 ",
    "Extreme": "--max-performance",
    "Auto": "--power-saving"
}

if not os.path.exists('Logs'):
    os.mkdir('Logs')

logging.basicConfig(filename='Logs/UXTU4Mac.log', filemode='w', encoding='utf-8',
                    level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logging.getLogger().addHandler(console_handler)

def get_system_info(command, use_sudo=False):
    if use_sudo:
        cfg = ConfigParser()
        cfg.read(CONFIG_PATH)
        password = cfg.get('User', 'Password', fallback='')

        command = f"sudo -S {command}"
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate(input=password.encode())
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()

    return output.decode('utf-8').strip()

def print_system_info():
    clr_print_logo()
    logging.info("Device Information:")
    logging.info(f' - Name: {get_system_info("scutil --get ComputerName")}')
    logging.info(f' - Model (SMBios): {get_system_info("sysctl -n hw.model")}')
    logging.info(
        f""" - {get_system_info("system_profiler SPHardwareDataType | grep 'Serial Number'")}"""
    )
    logging.info(f' - macOS: {get_system_info("sysctl -n kern.osproductversion")} ({get_system_info("sysctl -n kern.osversion")})')

    logging.info("\nProcessor Information:")
    logging.info(
        f' - Processor: {get_system_info("sysctl -n machdep.cpu.brand_string")}'
    )

    cpu_family = get_system_info("Assets/ryzenadj -i | grep 'CPU Family'", use_sudo=True).strip()
    smu_version = get_system_info("Assets/ryzenadj -i | grep 'SMU BIOS Interface Version'", use_sudo=True).strip()
    
    logging.info(f' - {cpu_family}')
    logging.info(f' - {smu_version}')

    logging.info(f' - Cores: {get_system_info("sysctl -n hw.physicalcpu")}')
    logging.info(f' - Threads: {get_system_info("sysctl -n hw.logicalcpu")}')
    logging.info(
        f""" - {get_system_info("system_profiler SPHardwareDataType | grep 'L2'")}"""
    )
    logging.info(
        f""" - {get_system_info("system_profiler SPHardwareDataType | grep 'L3'")}"""
    )
    base_clock = float(get_system_info("sysctl -n hw.cpufrequency_max")) / (10**9)
    logging.info(" - Base clock: {:.2f} GHz".format(base_clock))
    logging.info(f' - Vendor: {get_system_info("sysctl -n machdep.cpu.vendor")}')
    logging.info(f' - Family: {get_system_info("sysctl -n machdep.cpu.family")}')
    logging.info(
        f' - Features: {get_system_info("sysctl -a | grep machdep.cpu.features").split(": ")[1]}'
    )
    logging.info("\nMemory Information:")
    memory = float(get_system_info("sysctl -n hw.memsize")) / (1024**3)
    logging.info(" - Total Ram: {:.2f} GB".format(memory))
    ram_info = get_system_info("system_profiler SPMemoryDataType")
    ram_info_lines = ram_info.split('\n')
    ram_slot_names = ["BANK","SODIMM","DIMM"]

    slot_info = []
    try:
        for i, line in enumerate(ram_info_lines):  
           if any(slot_name in line for slot_name in ram_slot_names): 
             slot_name = line.strip()
             size = ram_info_lines[i+2].strip().split(":")[1].strip()
             type = ram_info_lines[i+3].strip().split(":")[1].strip()
             speed = ram_info_lines[i+4].strip().split(":")[1].strip()
             manufacturer = ram_info_lines[i+5].strip().split(":")[1].strip()
             part_number = ram_info_lines[i+6].strip().split(":")[1].strip()
             serial_number = ram_info_lines[i+7].strip().split(":")[1].strip()
             slot_info.append((slot_name, size, type, speed, manufacturer, part_number, serial_number))

        for i in range(0, len(slot_info), 2):
            logging.info(
                f" - Size: {slot_info[i][1]}/{slot_info[i + 1][1] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Type: {slot_info[i][2]}/{slot_info[i + 1][2] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Speed: {slot_info[i][3]}/{slot_info[i + 1][3] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Manufacturer: {slot_info[i][5]}/{slot_info[i + 1][5] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Status: {slot_info[i][4]}/{slot_info[i + 1][4] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Part Number: {slot_info[i][6]}/{slot_info[i + 1][6] if i + 1 < len(slot_info) else 'N/A'}"
            )
    except:
        logging.info("Pardon me for my horrible search for displaying RAM information")

    if has_battery := get_system_info(
        "system_profiler SPPowerDataType | grep 'Battery Information'"
    ):
        logging.info("\nBattery Information:")
        logging.info(
            f""" - {get_system_info("system_profiler SPPowerDataType | grep 'Manufacturer'")}"""
        )
        logging.info(
            f""" - {get_system_info("system_profiler SPPowerDataType | grep 'Device'")}"""
        )
        logging.info(" - State of Charge (%): {}".format(get_system_info("pmset -g batt | egrep '([0-9]+\\%).*' -o --colour=auto | cut -f1 -d';'")))
        logging.info(
            f""" - {get_system_info("system_profiler SPPowerDataType | grep 'Cycle Count'")}"""
        )
        logging.info(
            f""" - {get_system_info("system_profiler SPPowerDataType | grep 'Full Charge Capacity'")}"""
        )
        logging.info(
            f""" - {get_system_info("system_profiler SPPowerDataType | grep 'Condition'")}"""
        )
    logging.info("If you failed to get your hardware information, do `sudo purge` \nor remove RestrictEvents.kext")
    input("Press Enter to go back to the main menu...")
    
def clr_print_logo():
    os.system('clear')
    logging.info("""
    ██╗   ██╗██╗  ██╗████████╗██╗   ██╗██╗  ██╗███╗   ███╗ █████╗  ██████╗
    ██║   ██║╚██╗██╔╝╚══██╔══╝██║   ██║██║  ██║████╗ ████║██╔══██╗██╔════╝
    ██║   ██║ ╚███╔╝    ██║   ██║   ██║███████║██╔████╔██║███████║██║
    ██║   ██║ ██╔██╗    ██║   ██║   ██║╚════██║██║╚██╔╝██║██╔══██║██║
    ╚██████╔╝██╔╝ ██╗   ██║   ╚██████╔╝     ██║██║ ╚═╝ ██║██║  ██║╚██████╗
     ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝      ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝
    Special Beta Program 3
    Version: {}
    """.format(LOCAL_VERSION))

def main_menu():
    clr_print_logo()
    logging.info("1. Apply preset")
    logging.info("2. Settings")
    logging.info("")
    logging.info("I. Install Kexts and dependencies (Beta)")
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
    logging.info("Maintainer: GorouFlex")
    logging.info("CLI: GorouFlex")
    logging.info("GUI: NotchApple1703")
    logging.info("----------------------------")
    logging.info("")
    logging.info("1. Open GitHub repo")
    logging.info("2. Change log")
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
    
    while True:
        subprocess.run("sudo -k", shell=True)
        password = getpass.getpass("Enter your sudo password: ")
        sudo_check_command = f"echo '{password}' | sudo -S ls /"
        sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if sudo_check_process.returncode == 0:
            break
        else:
            logging.info("Incorrect sudo password. Please try again.")

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
        cfg.set('User', 'SkipCFU', '0')
                
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    except ValueError:
        logging.info("Invalid input. Please enter a number.")
        sys.exit(-1)

def welcome_tutorial():
    clr_print_logo()
    logging.info("Welcome to UXTU4Mac")
    logging.info("This tool was created by GorouFlex and is still in development.")
    logging.info("Based on RyzenAdj for AMD APU Ryzen and inspired by UXTU, I've created a version of UXTU specifically for macOS!")
    logging.info("Since this might be your first time using this tool, let's dive in!")
    input("Press Enter to continue")
    clr_print_logo()
    create_cfg()
    clr_print_logo()
    install_kext_menu()

def edit_config(config_path):
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)
    if 'NVRAM' in config and 'Add' in config['NVRAM'] and '7C436110-AB2A-4BBB-A880-FE41995C9F82' in config['NVRAM']['Add']:
        if 'boot-args' in config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']:
            boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
            if 'debug=0x144' not in boot_args:
                config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args'] = boot_args + ' debug=0x144'
        config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['csr-active-config'] = base64.b64decode('fwgAAA==')
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

def install_kext_menu():
    clr_print_logo()
    logging.info("Install kext and dependencies (Beta):")
    logging.info("")
    logging.info("1. Auto (Using default path e.g /Volumes/EFI/EFI/OC)")
    logging.info("")
    logging.info("B. Back")
    logging.info("")
    logging.info("If you are failed to install kexts and dependencies automatically than you can do it manually")
    logging.info("1. Add `DirectHW.kext` from `Assets/Kexts` to `EFI\OC\Kexts` and do a snapshot \nto config.plist")
    logging.info("2. Disable SIP (<`7F080000`>) at `csr-active-config`")
    logging.info("3. Add `debug=0x44` or `debug=0x144` to `boot-args`")
    logging.info("")

    choice = input("Option (default is 1): ")

    if choice == "1":
        install_kext_auto()
   # elif choice == "2":
     #   install_kext_manual()
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid choice. Please enter a valid option.")


def install_kext_auto():
    clr_print_logo()
    logging.info("Installing kext (Auto)...")

    script_directory = os.path.dirname(os.path.realpath(__file__))

    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')

    try:
        subprocess.run(["sudo", "-S", "diskutil", "mount", "EFI"], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to mount EFI partition: {e}")
        return

    try:

        kext_source_path = os.path.join(script_directory, "Assets/Kexts/DirectHW.kext")
        kext_destination_path = "/Volumes/EFI/EFI/OC/Kexts"

        subprocess.run(["sudo", "-S", "cp", "-r", kext_source_path, kext_destination_path], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to move DirectHW.kext: {e}")
        return

    oc_path = os.path.join("/Volumes/EFI/EFI/OC")
    if not os.path.exists(oc_path):
        logging.error("OC folder does not exist!")
        subprocess.run(["sudo", "diskutil", "unmount", "force", "EFI"], input=password.encode(), check=True)
        return

    config_path = os.path.join("/Volumes/EFI/EFI/OC/config.plist")
    ocsnapshot_script_path = os.path.join(script_directory, "Assets/OCSnapshot/OCSnapshot.py")

    subprocess.run(["python3", ocsnapshot_script_path, "-s", oc_path, "-i", config_path])
    edit_config(config_path)
    logging.info("Add boot-args and moodded SIP success")
    subprocess.run(["sudo", "diskutil", "unmount", "force", "EFI"], input=password.encode(), check=True)

    logging.info("Kext and dependencies installation completed.")
    input("Press Enter to go back main menu")
    
def read_cfg() -> str:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg.get('User', 'Mode', fallback='')

def check_cfg_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        welcome_tutorial()
        return

    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    
    if not cfg.has_section('User'):
        welcome_tutorial()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def check_updates():
    try:
      latest_version = get_latest_ver()
    except:
      clr_print_logo()
      logging.info("No Internet connection, try again")
    if LOCAL_VERSION < latest_version:
        clr_print_logo()
        logging.info("A new update is available! Please visit the following link for details:")
        logging.info(LATEST_VERSION_URL)
        sys.exit()
    elif LOCAL_VERSION > latest_version:
        clr_print_logo()
        logging.info("Welcome to UXTU4Mac Beta Program.")
        logging.info("This build may not be as stable as expected. Only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            logging.info("Quitting...")


def run_cmd(args, user_mode):
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    command = ["sudo", "-S", "Assets/ryzenadj"] + args.split()
    stop = False

    def check_input():
        nonlocal stop
        while True:
            i = input().lower()
            if i == 'b':
                stop = True
                break

    thread = threading.Thread(target=check_input)
    thread.start()

    while not stop:
        
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.info(f"Error: {result.stderr.decode()}")
        time.sleep(3)
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        logging.info("Script will be reapplied every 3 seconds")
        logging.info("Press B then Enter to go back the main menu")
        logging.info("------ RyzenAdj Log ------")
  #  logging.info("Press B then Enter to go back the main menu")
    thread.join()

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
         check_updates()
        
    check_cfg_integrity()
    user_mode = read_cfg()

    if user_mode:
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        run_cmd(PRESETS[user_mode], user_mode)

    while True:                
        main_menu()
        choice = input("Option: ")
        if choice == "1":
            clr_print_logo()
            logging.info("Apply Preset:")
            logging.info("1. Load from config file")
            logging.info("2. Custom preset (Beta)")
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
        elif choice.lower() == "i":
           install_kext_menu()
        elif choice.lower() == "h":
            print_system_info()
        elif choice.lower() == "a":
            info()
        elif choice.lower() == "q":
            sys.exit()
        else:
            logging.info("Invalid choice. Please enter a valid option.")
                
if __name__ == "__main__":
    main()
