import os, time, subprocess, getpass, webbrowser, logging, sys, binascii
import urllib.request, plistlib, base64, json, select
from configparser import ConfigParser

CONFIG_PATH = 'Assets/config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.2.3"

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=70 --stapm-limit=6000  --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Balance": "--tctl-temp=95 --apu-skin-temp=70 --stapm-limit=22000  --fast-limit=24000 --stapm-time=64 --slow-limit=22000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Performance": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=28000  --fast-limit=28000 --stapm-time=64 --slow-limit=28000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Extreme": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=30000  --fast-limit=34000 --stapm-time=64 --slow-limit=32000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "AC": "--max-performance",
    "DC": "--power-saving"
}

os.makedirs('Logs', exist_ok=True)
logging.basicConfig(filename='Logs/UXTU4Mac.log', filemode='w', encoding='utf-8',
                    level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler())
cfg = ConfigParser()
cfg.read(CONFIG_PATH)
current_dir = os.path.dirname(os.path.realpath(__file__))
command_file = os.path.join(current_dir, 'UXTU4Mac.command')
command_file_name = os.path.basename(command_file)

def clear():
    subprocess.call('clear', shell=True)
    logging.info(r"""    __  ___  __________  ______ __  ___
   / / / / |/_/_  __/ / / / / //  |/  /__ _____
  / /_/ />  <  / / / /_/ /_  _/ /|_/ / _ `/ __/
  \____/_/|_| /_/  \____/ /_//_/  /_/\_,_/\__/ """)
    logging.info(
        f'  {get_hardware_info("sysctl -n machdep.cpu.brand_string")}'
    )
    logging.info(f"  Version: {LOCAL_VERSION} by GorouFlex")
    logging.info("")
    
def get_hardware_info(command, use_sudo=False):
    password = cfg.get('User', 'Password', fallback='')
    if use_sudo:
        command = f"sudo -S {command}"
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate(input=password.encode())
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()
    return output.decode('utf-8').strip()

def hardware_info():
    clear()
    logging.info("\nProcessor Information:")
    logging.info(
        f' - Processor: {get_hardware_info("sysctl -n machdep.cpu.brand_string")}'
    )
    cpu_family = get_hardware_info("Assets/ryzenadj -i | grep 'CPU Family'", use_sudo=True).strip()
    smu_version = get_hardware_info("Assets/ryzenadj -i | grep 'SMU BIOS Interface Version'", use_sudo=True).strip()
    if cpu_family:
        logging.info(f' - {cpu_family}')
    if smu_version:
        logging.info(f' - {smu_version}')
    logging.info(f' - Cores: {get_hardware_info("sysctl -n hw.physicalcpu")}')
    logging.info(f' - Threads: {get_hardware_info("sysctl -n hw.logicalcpu")}')
    logging.info(
        f""" - {get_hardware_info("system_profiler SPHardwareDataType | grep 'L2'")}"""
    )
    logging.info(
        f""" - {get_hardware_info("system_profiler SPHardwareDataType | grep 'L3'")}"""
    )
    base_clock = float(get_hardware_info("sysctl -n hw.cpufrequency_max")) / (10**9)
    logging.info(" - Base clock: {:.2f} GHz".format(base_clock))
    logging.info(f' - Vendor: {get_hardware_info("sysctl -n machdep.cpu.vendor")}')
    logging.info(
        f' - Instruction: {get_hardware_info("sysctl -a | grep machdep.cpu.features").split(": ")[1]}'
    )
    logging.info("\nMemory Information:")
    memory = float(get_hardware_info("sysctl -n hw.memsize")) / (1024**3)
    logging.info(" - Total of RAM: {:.2f} GB".format(memory))
    ram_info = get_hardware_info("system_profiler SPMemoryDataType")
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
                f" - Size: {slot_info[i][1]} / {slot_info[i + 1][1] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Type: {slot_info[i][2]} / {slot_info[i + 1][2] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Speed: {slot_info[i][3]} / {slot_info[i + 1][3] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Manufacturer: {slot_info[i][5]} / {slot_info[i + 1][5] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Status: {slot_info[i][4]} / {slot_info[i + 1][4] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Part Number: {slot_info[i][6]} / {slot_info[i + 1][6] if i + 1 < len(slot_info) else 'N/A'}"
            )
    except:
        logging.info("Pardon me for my horrible search for displaying RAM information")
    if has_battery := get_hardware_info(
        "system_profiler SPPowerDataType | grep 'Battery Information'"
    ):
        logging.info("\nBattery Information:")
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Manufacturer'")}"""
        )
        logging.info(" - State of Charge (%): {}".format(get_hardware_info("pmset -g batt | egrep '([0-9]+\\%).*' -o --colour=auto | cut -f1 -d';'")))
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Cycle Count'")}"""
        )
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Full Charge Capacity'")}"""
        )
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Condition'")}"""
        )
    logging.info("")
    input("Press Enter to continue...")

def welcome_tutorial():
    if not cfg.has_section('User'):
        cfg.add_section('User')
    if not cfg.has_section('Settings'):
        cfg.add_section('Settings')
    clear()
    logging.info("--------------- Welcome to UXTU4Mac ---------------")
    logging.info("Designed for AMD Zen-based processors on macOS")
    logging.info("Based on RyzenAdj and inspired by UXTU")
    logging.info("Let's get started with some initial setup ~~~")
    input("Press Enter to continue...")
    clear()
    while True:
        subprocess.run("sudo -k", shell=True)
        password = getpass.getpass("Enter your sudo (login) password: ")
        sudo_check_command = f"echo '{password}' | sudo -S ls /"
        sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if sudo_check_process.returncode == 0:
            break
        else:
            logging.info("Incorrect sudo password. Please try again.")
    check_command = f"osascript -e 'tell application \"System Events\" to get the name of every login item' | grep {command_file_name}"
    login_enabled = subprocess.call(check_command, shell=True, stdout=subprocess.DEVNULL) == 0
    if not login_enabled:
        start_with_macos = input("Do you want this script to start with macOS? (Login Items) (y/n): ").lower().strip()
        if start_with_macos == 'y':
            command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
            subprocess.call(command, shell=True)
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    try:
        cfg.set('User', 'Password', password)
        cfg.set('Settings', 'Time', '30')
        cfg.set('Settings', 'SoftwareUpdate', '1')
        cfg.set('Settings', 'ReApply', '0')
        cfg.set('Settings', 'DynamicMode', '0')
        cfg.set('Settings', 'SIP', '03080000')
    except ValueError:
        logging.info("Invalid option.")
        raise SystemExit
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    preset_cfg()
    clear()
    if not check_run():
       install_menu()
       
def settings():
    options = {
        "1": preset_cfg,
        "2": sleep_cfg,
        "3": dynamic_cfg,
        "4": reapply_cfg,
        "5": login_cfg,
        "6": cfu_cfg,
        "7": pass_cfg,
        "8": sip_cfg,
        "i": install_menu,
        "r": reset,
        "b": "break"
    }
    while True:
        clear()
        logging.info("--------------- Settings ---------------")
        logging.info("1. Preset\n2. Sleep time")
        logging.info("3. Dynamic mode\n4. Auto reapply")
        logging.info("5. Run on Startup\n6. Software update")
        logging.info("7. Sudo password\n8. SIP flags\n")
        logging.info("I. Install UXTU4Mac dependencies")
        logging.info("R. Reset all saved settings")
        logging.info("B. Back")
        settings_choice = input("Option: ").lower().strip()
        action = options.get(settings_choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def reapply_cfg():
    while True:
        clear()
        logging.info("--------------- Auto reapply ---------------")
        reapply_enabled = cfg.get('Settings', 'ReApply', fallback='0') == '1'
        logging.info("Status: Enabled" if reapply_enabled else "Status: Disabled")
        logging.info("\n1. Enable Auto reapply\n2. Disable Auto reapply")
        logging.info("B. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'ReApply', '1')
        elif choice == "2":
            cfg.set('Settings', 'ReApply', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def sip_cfg():
    while True:
        clear()
        logging.info("--------------- SIP flags---------------")
        logging.info("(Change your required SIP flags)")
        SIP = cfg.get('Settings', 'SIP', fallback='03080000')
        logging.info(f"Current required SIP: {SIP}")
        logging.info("\n1. Change SIP flags")
        logging.info("B. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            logging.info("Caution: Must have at least ALLOW_UNTRUSTED_KEXTS (0x1)")
            SIP = input("Enter your required SIP Flags: ")
            cfg.set('Settings', 'SIP', SIP)
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def dynamic_cfg():
    while True:
        clear()
        dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'
        logging.info("--------------- Dynamic Mode ---------------")
        logging.info("Status: Enabled" if dm_enabled else "Status: Disabled")
        logging.info("\n1. Enable Dynamic Mode\n2. Disable Dynamic Mode\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'DynamicMode', '1')
        elif choice == "2":
            cfg.set('Settings', 'DynamicMode', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def sleep_cfg():
    while True:
        clear()
        time = cfg.get('Settings', 'Time', fallback='30')
        logging.info("--------------- Sleep time ---------------")
        logging.info(f"Auto reapply every: {time} seconds")
        logging.info("\n1. Change\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            set_time = input("Enter your auto reapply time (Default is 30s): ")
            cfg.set('Settings', 'Time', set_time)
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")

def pass_cfg():
    while True:
        clear()
        pswd = cfg.get('User', 'Password', fallback='')
        logging.info("--------------- Sudo password ---------------")
        logging.info(f"Current sudo (login) password: {pswd}")
        logging.info("\n1. Change password\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            while True:
                subprocess.run("sudo -k", shell=True)
                password = getpass.getpass("Enter your sudo (login) password: ")
                sudo_check_command = f"echo '{password}' | sudo -S ls /"
                sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if sudo_check_process.returncode == 0:
                    cfg.set('User', 'Password', password)
                    with open(CONFIG_PATH, 'w') as config_file:
                        cfg.write(config_file)
                    break
                else:
                    logging.info("Incorrect sudo password. Please try again.")
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")

def login_cfg():
    while True:
        clear()
        check_command = f"osascript -e 'tell application \"System Events\" to get the name of every login item' | grep {command_file_name}"
        login_enabled = subprocess.call(check_command, shell=True, stdout=subprocess.DEVNULL) == 0
        logging.info("--------------- Run on Startup ---------------")
        logging.info(f"Status: {'Enable' if login_enabled else 'Disable'}")
        logging.info("\n1. Enable Run on Startup\n2. Disable Run on Startup\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            if not login_enabled:
               command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
               subprocess.call(command, shell=True)
            else:
                logging.info("You already added this script to Login Items.")
                input("Press Enter to continue.")
        elif choice == "2":
            if login_enabled:
              command = f"osascript -e 'tell application \"System Events\" to delete login item \"{command_file_name}\"'"
              subprocess.call(command, shell=True)
            else:
              logging.info("Cannot remove this script because it does not exist in Login Items.")
              input("Press Enter to continue.")
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue.")

def cfu_cfg():
    while True:
        clear()
        cfu_enabled = cfg.get('Settings', 'SoftwareUpdate', fallback='1') == '1'
        logging.info("--------------- Software update ---------------")
        logging.info(f"Status: {'Enabled' if cfu_enabled else 'Disabled'}")
        logging.info("\n1. Enable Software update\n2. Disable Software update\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'SoftwareUpdate', '1')
        elif choice == "2":
            cfg.set('Settings', 'SoftwareUpdate', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue.")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def preset_cfg():
    while True:
        clear()
        logging.info("--------------- Preset ---------------")
        logging.info("Preset:")
        for i, mode in enumerate(PRESETS, start=1):
            logging.info(f"{i}. {mode}")
        logging.info("\nD. Dynamic Mode")
        logging.info("C. Custom (Beta)")
        logging.info("B. Back")
        logging.info("We recommend using the Dynamic Mode for normal tasks and better power management")
        choice = input("Option: ").lower().strip()
        if choice == 'c':
            custom_args = input("Enter your custom arguments: ")
            cfg.set('User', 'Mode', 'Custom')
            cfg.set('User', 'CustomArgs', custom_args)
            logging.info("Set preset successfully!")
            input("Press Enter to continue...")
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
            break
        elif choice == 'd':
            cfg.set('User', 'Mode', 'Balance')
            cfg.set('Settings', 'DynamicMode', '1')
            cfg.set('Settings', 'ReApply', '1')
            logging.info("Set preset successfully!")
            input("Press Enter to continue...")
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
            break
        elif choice == 'b':
            return
        else:
            try:
                preset_number = int(choice)
                preset_name = list(PRESETS.keys())[preset_number - 1]
                cfg.set('User', 'Mode', preset_name)
                logging.info("Set preset successfully!")
                input("Press Enter to continue...")
                with open(CONFIG_PATH, 'w') as config_file:
                    cfg.write(config_file)
                break
            except ValueError:
                logging.info("Invalid option.")
                input("Press Enter to continue")

def edit_config(config_path):
    SIP = cfg.get('Settings', 'SIP', fallback='03080000')
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)
    if 'NVRAM' in config and 'Add' in config['NVRAM'] and '7C436110-AB2A-4BBB-A880-FE41995C9F82' in config['NVRAM']['Add']:
        if 'boot-args' in config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']:
            boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
            if 'debug=0x144' not in boot_args:
                config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args'] = f'{boot_args} debug=0x144'
        SIP_bytes = binascii.unhexlify(SIP)
        config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['csr-active-config'] = SIP_bytes
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

def install_menu():
    clear()
    logging.info("UXTU4Mac dependencies\n")
    logging.info("1. Auto install (Default path: /Volumes/EFI/EFI/OC)\n2. Manual install (Specify your config.plist path)\n")
    logging.info("B. Back")
    choice = input("Option (default is 1): ").strip()
    if choice == "1":
        install_auto()
    elif choice == "2":
        install_manual()
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid option. Please try again.")
        input("Press Enter to continue...")
        
def install_auto():
    clear()
    logging.info("Installing UXTU4Mac dependencies (Auto)...")
    password = cfg.get('User', 'Password', fallback='')
    try:
        subprocess.run(["sudo", "-S", "diskutil", "mount", "EFI"], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to mount EFI partition: {e}")
        logging.error("Please run in Manual mode.")
        input("Press Enter to continue...")
        return
    oc_path = os.path.join("/Volumes/EFI/EFI/OC")
    if not os.path.exists(oc_path):
        logging.error("OC folder does not exist!")
        input("Press Enter to continue...")
        return
    config_path = os.path.join("/Volumes/EFI/EFI/OC/config.plist")
    edit_config(config_path)
    logging.info("Successfully updated boot-args and SIP settings.")
    logging.info("UXTU4Mac dependencies installation completed.")
    choice = input("Do you want to restart your computer to take effects? (y/n)").lower()
    if choice == "y":
        input("Saved your current work before restarting. Press Enter to continue")
        restart_command = '''osascript -e 'tell app "System Events" to restart' '''
        subprocess.call(restart_command, shell=True)

def install_manual():
    clear()
    logging.info("Installing UXTU4Mac dependencies (Manual)...")
    password = cfg.get('User', 'Password', fallback='')
    config_path = input("Please drag and drop the target plist: ").strip()
    if not os.path.exists(config_path):
        logging.error(f"The specified path '{config_path}' does not exist.")
        input("Press Enter to continue...")
        return
    edit_config(config_path)
    logging.info("Successfully updated boot-args and SIP settings.")
    logging.info("UXTU4Mac dependencies installation completed.")
    choice = input("Do you want to restart your computer to take effects? (y/n)").lower()
    if choice == "y":
        input("Saved your current work before restarting. Press Enter to continue")
        restart_command = '''osascript -e 'tell app "System Events" to restart' '''
        subprocess.call(restart_command, shell=True)

def reset():
    os.remove(CONFIG_PATH)
    welcome_tutorial()
    
def read_cfg() -> str:
    return cfg.get('User', 'Mode', fallback='')

def check_cfg_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        welcome_tutorial()
        return
    required_keys_user = ['password', 'mode']
    required_keys_settings = ['time', 'dynamicmode', 'sip', 'reapply', 'softwareupdate']
    if not cfg.has_section('User') or not cfg.has_section('Settings') or \
    any(key not in cfg['User'] for key in required_keys_user) or \
    any(key not in cfg['Settings'] for key in required_keys_settings):
      reset()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def get_changelog():
    request = urllib.request.Request(GITHUB_API_URL)
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data['body']

def check_run():
    SIP = cfg.get('Settings', 'SIP', fallback='03080000')
    result = subprocess.run(['nvram', 'boot-args'], capture_output=True, text=True)
    if 'debug=0x144' not in result.stdout:
        return False
    result = subprocess.run(['nvram', 'csr-active-config'], capture_output=True, text=True)
    return SIP in result.stdout.replace('%', '')
            
def updater():
    clear()
    changelog = get_changelog()
    logging.info("--------------- UXTU4Mac Software Update ---------------")
    logging.info("A new update is available!")
    logging.info(
        f"Changelog for the latest version ({get_latest_ver()}):\n{changelog}"
    )
    logging.info("Do you want to update? (y/n): ")
    choice = input("Option: ").lower().strip()
    if choice == "y":
        subprocess.run(["python3", "Assets/SU.py"])
        logging.info("Updating...")
        logging.info("Update complete. Restarting the application, please close this window...")
        command_file_path = os.path.join(os.path.dirname(__file__), 'UXTU4Mac.command')
        subprocess.Popen(['open', command_file_path])
    elif choice == "n":
        logging.info("Skipping update...")
    else:
        logging.info("Invalid option.")
    raise SystemExit

def check_updates():
    clear()
    max_retries = 10
    for i in range(max_retries):
        try:
            latest_version = get_latest_ver()
            if LOCAL_VERSION < latest_version:
                updater()
            break
        except:
            if i < max_retries - 1:
                logging.info(f"Failed to fetch latest version. Retrying {i+1}/{max_retries}...")
                time.sleep(5)
            else:
                result = input("Do you want to skip the check for updates? (y/n): ").lower().strip()
                if result != "y":
                    logging.info("Quitting...")
                    raise SystemExit

def about():
    options = {
        "1": lambda: webbrowser.open("https://www.github.com/AppleOSX/UXTU4Mac"),
        "f": updater,
        "b": "break"
    }
    while True:
        clear()
        logging.info("About UXTU4Mac")
        logging.info("The Dynamic Update (2F16CI)")
        logging.info("----------------------------")
        logging.info("Maintainer: GorouFlex\nCLI: GorouFlex")
        logging.info("GUI: NotchApple1703\nAdvisor: NotchApple1703")
        logging.info("Command file: CorpNewt")
        logging.info("----------------------------")
        logging.info(f"F. Force update to the latest version ({get_latest_ver()})")
        logging.info("\nB. Back")
        choice = input("Option: ").lower().strip()
        action = options.get(choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def preset_menu():
    clear()
    logging.info("Apply power management settings:")
    logging.info("1. Load saved settings from config file\n2. Load from available premade preset\n\nD. Dynamic Mode")
    logging.info("B. Back")
    preset_choice = input("Option: ").strip()
    if preset_choice == "1":
        if user_mode := read_cfg():
            if user_mode in PRESETS:
                apply_smu(PRESETS[user_mode], user_mode)
            else:
                apply_smu(user_mode, user_mode)
        else:
            logging.info("Config file is missing or invalid")
            logging.info("Reset config file..")
            input("Press Enter to continue...")
            welcome_tutorial()
    elif preset_choice == "2":
        clear()
        logging.info("Select a premade preset:")
        for i, mode in enumerate(PRESETS, start=1):
            logging.info(f"{i}. {mode}")
        preset_number = input("Option: ").strip()
        try:
            preset_number = int(preset_number)
            if 1 <= preset_number <= len(PRESETS):
                selected_preset = list(PRESETS.keys())[preset_number - 1]
                clear()
                user_mode = selected_preset
                apply_smu(PRESETS[user_mode], user_mode)
            else:
                logging.info("Invalid option.")
                input("Press Enter to continue...")
        except ValueError:
            logging.info("Invalid input. Please enter a number.")
    elif preset_choice.lower() == "d":
         last_mode = cfg.get('Settings', 'DynamicMode', fallback='0')
         last_apply = cfg.get('Settings', 'ReApply', fallback='0')
         cfg.set('Settings', 'DynamicMode', '1')
         cfg.set('Settings', 'ReApply', '1')
         apply_smu(PRESETS['Balance'], 'Balance')
         cfg.set('Settings', 'DynamicMode', last_mode)
         cfg.set('Settings', 'ReApply', last_apply)
    elif preset_choice.lower() == "b":
        return
    else:
        logging.info("Invalid option.")
        
def apply_smu(args, user_mode):
    if not check_run():
        clear()
        logging.info("Cannot run RyzenAdj because your computer is missing debug=0x144 or required SIP is not SET yet\nPlease run Install UXTU4Mac dependencies under Setting \nand restart after install.")
        input("Press Enter to continue...")
        return
    sleep_time = cfg.get('Settings', 'Time', fallback='30')
    password = cfg.get('User', 'Password', fallback='')
    reapply = cfg.get('Settings', 'ReApply', fallback='0')
    dynamic = cfg.get('Settings', 'dynamicmode', fallback='0')
    prev_mode = None
    if reapply == '1':
      while True:
        if dynamic == '1':
            has_battery = subprocess.check_output(["system_profiler", "SPPowerDataType", "|", "grep", "'Battery Information'"]).decode("utf-8")
            if has_battery:
                battery_status = subprocess.check_output(["pmset", "-g", "batt"]).decode("utf-8")
                if 'AC Power' in battery_status:
                    user_mode = 'Extreme'
                else:
                    user_mode = 'Eco'
            else:
                user_mode = 'Extreme'
        if prev_mode == user_mode and dynamic == '1':
            for _ in range(int(float(sleep_time))):
                for _ in range(1):
                    time.sleep(1)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = sys.stdin.readline()
                        if line.lower().strip() == 'b':
                            return
            continue
        prev_mode = user_mode
        clear()
        if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", "Assets/ryzenadj"] + custom_args.split()
        else:
            args = PRESETS[user_mode]
            command = ["sudo", "-S", "Assets/ryzenadj"] + args.split()
        logging.info(f"Using preset: {user_mode}")
        dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'
        if dm_enabled:
            logging.info("Dynamic mode: Enabled")
        else:
            logging.info("Dynamic mode: Disabled")
        logging.info(f"Script will check and auto reapply if need every {sleep_time} seconds")
        logging.info("Press B then Enter to go back to the main menu")
        logging.info("--------------- RyzenAdj Log ---------------")
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.info(f"{result.stderr.decode()}")
        for _ in range(int(float(sleep_time))):
            for _ in range(1):
                time.sleep(1)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.lower().strip() == 'b':
                        return
    else:
          clear()
          if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", "Assets/ryzenadj"] + custom_args.split()
          else:
            args = PRESETS[user_mode]
            command = ["sudo", "-S", "Assets/ryzenadj"] + args.split()
          logging.info(f"Using preset: {user_mode}")
          logging.info("--------------- RyzenAdj Log ---------------")
          result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          logging.info(result.stdout.decode())
          if result.stderr:
            logging.info(f"{result.stderr.decode()}")
          input("Press Enter to continue...")
          
def main():
    check_cfg_integrity()
    if cfg.get('Settings', 'SoftwareUpdate', fallback='1') == '1':
        check_updates()
    if user_mode := read_cfg():
        if user_mode in PRESETS:
            apply_smu(PRESETS[user_mode], user_mode)
        else:
            apply_smu(user_mode, user_mode)
    while True:
        clear()
        options = {
            "1": preset_menu,
            "2": settings,
            "h": hardware_info,
            "a": about,
            "q": lambda: sys.exit("\nThanks for using UXTU4Mac\nHave a nice day!"),
        }
        logging.info("1. Apply power management settings\n2. Settings")
        logging.info("")
        logging.info("H. Hardware Information")
        logging.info("A. About UXTU4Mac")
        logging.info("Q. Quit")
        choice = input("Option: ").lower().strip()
        if action := options.get(choice):
            action()
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
                
if __name__ == "__main__":
    main()
