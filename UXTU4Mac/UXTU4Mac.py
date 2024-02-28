import os, sys, time, subprocess, getpass, webbrowser, logging
import urllib.request, plistlib, threading, base64, json, hashlib
from configparser import ConfigParser

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.1.5"

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
    logging.info("Device information:")
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
    if cpu_family:
        logging.info(f' - {cpu_family}')
    if smu_version:
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
    logging.info(f' - CPU Vendor: {get_system_info("sysctl -n machdep.cpu.vendor")}')
    logging.info(f' - Family model: {get_system_info("sysctl -n machdep.cpu.family")}')
    logging.info(
        f' - CPU instruction: {get_system_info("sysctl -a | grep machdep.cpu.features").split(": ")[1]}'
    )
    logging.info("\nMemory information:")
    memory = float(get_system_info("sysctl -n hw.memsize")) / (1024**3)
    logging.info(" - Total of Ram: {:.2f} GB".format(memory))
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
    logging.info("")
    logging.info("UXTU4Mac dependencies:")
    result = subprocess.run(['kextstat'], capture_output=True, text=True)
    if 'DirectHW' not in result.stdout:
        print(" - DirectHW.kext: Missing")
    else:
        print(" - DirectHW.kext: OK")
    result = subprocess.run(['nvram', 'boot-args'], capture_output=True, text=True)
    if 'debug=0x144' not in result.stdout:
        print(" - debug=0x144: Missing")
    else:
        print(" - debug=0x144: OK")
    result = subprocess.run(['nvram', 'csr-active-config'], capture_output=True, text=True)
    if '%7f%08%00%00' not in result.stdout:
        print(" - 7F080000 SIP: Not set")
    else:
        print(" - 7F080000 SIP: OK")    
    logging.info("")
    logging.info("If you fail to retrieve your hardware information, run `sudo purge` \nor remove RestrictEvent.kext")
    input("Press Enter to continue...")

def clr_print_logo():
    os.system('clear')
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
    logging.info("I. Install kexts and dependencies")
    logging.info("A. About UXTU4Mac")
    logging.info("Q. Quit")

def about_menu():
    clr_print_logo()
    logging.info("About UXTU4Mac")
    logging.info("Codename: AATUOSX")
    logging.info("The Loop Update (1C2C7)")
    logging.info("----------------------------")
    logging.info("Maintainer: GorouFlex")
    logging.info("CLI: GorouFlex")
    logging.info("GUI: NotchApple1703")
    logging.info("OCSnapshot: CorpNewt")
    logging.info("----------------------------")
    logging.info("1. Open GitHub repo")
    logging.info("2. Show changelog")
    logging.info("T. Tester list")
    logging.info(f"F. Force update to the latest version ({get_latest_ver()})")
    logging.info("")
    logging.info("B. Back")

def setting_menu():
    clr_print_logo()
    logging.info("------------ Settings ----------")
    logging.info("1. Preset setting")
    logging.info("2. FIP setting")
    logging.info("3. CFU setting")
    logging.info("4. Login Items setting")
    logging.info("5. Sudo Password setting")
    logging.info("6. Time Sleep setting")
    logging.info("")
    logging.info("B. Back")

def sleep_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ Time Sleep Setting ---------")
    logging.info("(Time sleep between next apply to SMU using ryzenAdj)")
    time = cfg.get('User', 'Time', fallback='10')
    logging.info(f"Time sleep: {time}")
    logging.info("")
    logging.info("1. Change time sleep")
    logging.info("")
    logging.info("B. Back")
    choice = input("Option: ")
    if choice == "1":
       set_time = input("Enter your sleep time (Default is 10s): ")
       cfg.set('User', 'Time', set_time)   
       with open(CONFIG_PATH, 'w') as config_file:
         cfg.write(config_file)
       input("Press Enter to continue...")
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")
    sleep_cfg()
    
def pass_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ Sudo Password Setting ---------")
    pswd = cfg.get('User', 'Password', fallback='')
    logging.info(f"Current sudo (login) password: {pswd}")
    logging.info("1. Change password")
    logging.info("")
    logging.info("B. Back")
    choice = input("Option: ")
    if choice == "1":
       while True:
         subprocess.run("sudo -k", shell=True)
         password = getpass.getpass("Enter your sudo (login) password: ")
         sudo_check_command = f"echo '{password}' | sudo -S ls /"
         sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)   
         if sudo_check_process.returncode == 0:
            break
         else:
           logging.info("Incorrect sudo password. Please try again.")
         cfg.set('User', 'Password', password)
         with open(CONFIG_PATH, 'w') as config_file:
           cfg.write(config_file)
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")
    pass_cfg()
    
def login_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ Login Items Setting ---------")
    logging.info("(Run script with macOS every startup)")
    login_enabled = cfg.get('User', 'LoginItems', fallback='1') == '1'
    if login_enabled:
        logging.info("Login Items status: OK")
    else:
        logging.info("Login Items status: Not set")
    logging.info("")
    logging.info("1. Enable Login Items")
    logging.info("2. Disable Login Items")
    logging.info("")
    logging.info("B. Back")
    choice = input("Option: ")
    if choice == "1":
        cfg.set('User', 'LoginItems', '1')
        with open(CONFIG_PATH, 'w') as config_file:
          cfg.write(config_file)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        command_file = os.path.join(current_dir, 'UXTU4Mac.command')
        command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
        subprocess.call(command, shell=True)
    elif choice == "2":
        cfg.set('User', 'LoginItems', '0')
        with open(CONFIG_PATH, 'w') as config_file:
          cfg.write(config_file)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        command_file = os.path.join(current_dir, 'UXTU4Mac.command')
        command = f'''
         osascript -e 'tell application "System Events"
         set login_items to the name of every login item
         if "{command_file}" is in login_items then
            delete login item "{command_file}"
         end if
        end tell'
        '''
        subprocess.call(command, shell=True)
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")
    login_cfg()
    
def cfu_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ Check For Updates Setting ---------")
    cfu_enabled = cfg.get('User', 'CFU', fallback='1') == '1'
    if cfu_enabled:
        logging.info("CFU status: Enabled")
    else:
        logging.info("CFU status: Disabled")
    logging.info("")
    logging.info("1. Enable CFU")
    logging.info("2. Disable CFU")
    logging.info("")
    logging.info("B. Back")
    choice = input("Option: ")
    if choice == "1":
       cfg.set('User', 'CFU', '1')   
       with open(CONFIG_PATH, 'w') as config_file:
         cfg.write(config_file)
    elif choice == "2":
       cfg.set('User', 'CFU', '0')   
       with open(CONFIG_PATH, 'w') as config_file:
         cfg.write(config_file)
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")
    cfu_cfg()

def fip_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ File Integrity Protection Setting ------------")
    fip_enabled = cfg.get('User', 'FIP', fallback='0') == '1'
    if fip_enabled:
        logging.info("FIP status: Enabled")
    else:
        logging.info("FIP status: Disabled")
    logging.info("")
    logging.info("1. Enable FIP")
    logging.info("2. Disable FIP")
    logging.info("")
    logging.info("B. Back")
    choice = input("Option: ")
    if choice == "1":
       cfg.set('User', 'FIP', '1')
       with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    elif choice == "2":
       cfg.set('User', 'FIP', '0')
       with open(CONFIG_PATH, 'w') as config_file:
         cfg.write(config_file)
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")
    fip_cfg()
    
def preset_cfg() -> None:
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    clr_print_logo()
    logging.info("------------ Preset Setting ------------")
    logging.info("Premade preset:")
    for i, mode in enumerate(PRESETS, start=1):
        logging.info(f"{i}. {mode}")
    logging.info("C. Custom (Beta)")
    logging.info("")
    logging.info("B. Back")
    logging.info("We recommend using the Auto preset for normal tasks and better power management based on your CPU usage, and the Extreme preset for unlocking full")
    logging.info("potential performance.")
    choice = input("Option: ")
    if choice.lower() == 'c':
        custom_args = input("Enter your custom arguments: ")
        cfg.set('User', 'Mode', 'Custom')
        cfg.set('User', 'CustomArgs', custom_args)
        logging.info("Set preset sucessfully!")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
        input("Press Enter to continue...")
    elif choice.lower() == 'b':
        return
    else:
        try:
            preset_number = int(choice)
            preset_name = list(PRESETS.keys())[preset_number - 1]
            cfg.set('User', 'Mode', preset_name)
            logging.info("Set preset sucessfully!")
            input("Press Enter to continue...")
        except ValueError:
            logging.info("Invalid Option.")
            input("Press Enter to continue...")
            preset_cfg()
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    
def welcome_tutorial():
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    cfg.add_section('User')
    clr_print_logo()
    logging.info("Welcome to UXTU4Mac!")
    logging.info("Created by GorouFlex, designed for AMD Zen-based processors on macOS.")
    logging.info("Based on RyzenAdj and inspired by UXTU.")
    logging.info("Let's get started with some initial setup.")
    input("Press Enter to continue...")
    clr_print_logo()
    while True:
      subprocess.run("sudo -k", shell=True)
      password = getpass.getpass("Enter your sudo (login) password: ")
      sudo_check_command = f"echo '{password}' | sudo -S ls /"
      sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)   
      if sudo_check_process.returncode == 0:
         break
      else:
         logging.info("Incorrect sudo password. Please try again.")
    login_items_setting = cfg.get('User', 'LoginItems', fallback='0')
    if login_items_setting == '0':
        start_with_macos = input("Do you want this script to start with macOS? (Login Items) (y/n): ").lower()
        if start_with_macos == 'y':
            login = "1"
            current_dir = os.path.dirname(os.path.realpath(__file__))
            command_file = os.path.join(current_dir, 'UXTU4Mac.command')
            command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
            subprocess.call(command, shell=True)
        else:
           login = "0"
    try:
       cfg.set('User', 'Password', password)
       cfg.set('User', 'LoginItems', login)
       cfg.set('User', 'CFU', '1')
       cfg.set('User', 'FIP', '0')
       cfg.set('User', 'Time', '10')
    except ValueError:
        logging.info("Invalid Option.")
        sys.exit(-1)
    with open(CONFIG_PATH, 'w') as config_file:
      cfg.write(config_file)
    preset_cfg()
    logging.info("Configuration file created successfully!")
    input("Press Enter to proceed to the next step...")
    clr_print_logo()
    install_kext_menu()

def edit_config(config_path):
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)
    if 'NVRAM' in config and 'Add' in config['NVRAM'] and '7C436110-AB2A-4BBB-A880-FE41995C9F82' in config['NVRAM']['Add']:
        if 'boot-args' in config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']:
            boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
            if 'debug=0x144' not in boot_args:
                config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82'][
                    'boot-args'
                ] = f'{boot_args} debug=0x144'
        config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['csr-active-config'] = base64.b64decode('fwgAAA==')
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

def install_kext_menu():
    clr_print_logo()
    logging.info("Install kext and dependencies")
    logging.info("")
    logging.info("1. Auto (Using default path: /Volumes/EFI/EFI/OC)")
    logging.info("2. Manual (Specify your config.plist path)")
    logging.info("")
    logging.info("B. Back")
    logging.info("")
    choice = input("Option (default is 1): ")
    if choice == "1":
        install_kext_auto()
    elif choice == "2":
        install_kext_manual()
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")

def install_kext_auto():
    clr_print_logo()
    logging.info("Installling kext and dependencies (Auto)...")
    script_directory = os.path.dirname(os.path.realpath(__file__))
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    try:
        subprocess.run(["sudo", "-S", "diskutil", "mount", "EFI"], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to mount EFI partition: {e}")
        logging.info("")
        logging.error("Please run in Manual mode.")
        input("Press Enter to continue...")
        return
    try:
        kext_source_path = os.path.join(script_directory, "Assets/Kexts/DirectHW.kext")
        kext_destination_path = "/Volumes/EFI/EFI/OC/Kexts"
        subprocess.run(["sudo", "-S", "cp", "-r", kext_source_path, kext_destination_path], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to move DirectHW.kext: {e}")
        logging.info("")
        logging.error("Please run in Manual mode.")
        input("Press Enter to continue...")
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
    logging.info("Successfully updated boot-args and SIP settings.")
    subprocess.run(["sudo", "diskutil", "unmount", "force", "EFI"], input=password.encode(), check=True)
    logging.info("EFI partition unmounted successfully.")
    logging.info("Kext and dependencies installation completed.")
    logging.info("Please restart your computer to take effect!")
    input("Press Enter to continue...")

def install_kext_manual():
    clr_print_logo()
    logging.info("Installing kext and dependencies (Manual)...")
    script_directory = os.path.dirname(os.path.realpath(__file__))
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')

    config_path = input("Please drag and drop the target plist:  ")
    config_path = config_path.strip()
    print(config_path)
    if not os.path.exists(config_path):
        print(f"Error: The specified path '{config_path}' does not exist.")
        return

    oc_path = os.path.dirname(config_path)
    kext_source_path = os.path.join(script_directory, "Assets/Kexts/DirectHW.kext")
    kext_destination_path = os.path.join(oc_path, "Kexts")

    subprocess.run(["sudo", "-S", "cp", "-r", kext_source_path, kext_destination_path], input=password.encode(), check=True)
    ocsnapshot_script_path = os.path.join(script_directory, "Assets/OCSnapshot/OCSnapshot.py")
    subprocess.run(["python3", ocsnapshot_script_path, "-s", oc_path, "-i", config_path])
    edit_config(config_path)
    logging.info("Successfully updated boot-args and SIP settings.")
    print("Kext and dependencies installation completed.")
    logging.info("Please restart your computer to take effect!")
    input("Press Enter to continue...")

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

def get_changelog():
    request = urllib.request.Request(GITHUB_API_URL)
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data['body']

def run_updater():
    clr_print_logo()
    changelog = get_changelog()
    logging.info("--------- UXTU4Mac Software Update ---------")
    logging.info("A new update is available!")
    logging.info(
        f"Changelog for the latest version ({get_latest_ver}):\n{changelog}"
    )
    logging.info("Do you want to update? (y/n): ")
    choice = input("Option: ").lower()

    if choice == "y":        
        subprocess.run(["python3", "Assets/Updater.py"])
        logging.info("Update complete. Restarting the application, please close this window...")
        restart_application()
    elif choice == "n":
        logging.info("Skipping update...")
        sys.exit(-1)
    else:
        logging.info("Invalid Option.")
        input("Press Enter to continue...")

def restart_application():
    command_file_path = os.path.join(os.path.dirname(__file__), 'UXTU4Mac.command')
    subprocess.Popen(['open', command_file_path])
    sys.exit()

def check_updates():
    try:
        latest_version = get_latest_ver()
    except:
        clr_print_logo()
        logging.info("No Internet connection, try again")
    if LOCAL_VERSION < latest_version:
        run_updater()
    elif LOCAL_VERSION > latest_version:
        clr_print_logo()
        logging.info("Welcome to UXTU4Mac Beta Program.")
        logging.info("This build may not be as stable as expected. Only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            logging.info("Quitting...")
            raise SystemExit

def check_kext():
    result = subprocess.run(['kextstat'], capture_output=True, text=True)
    if 'DirectHW' not in result.stdout:
        return False
    result = subprocess.run(['nvram', 'boot-args'], capture_output=True, text=True)
    if 'debug=0x144' not in result.stdout:
        return False
    result = subprocess.run(['nvram', 'csr-active-config'], capture_output=True, text=True)
    return '%7f%08%00%00' in result.stdout

def run_cmd(args, user_mode):
    if not check_kext():
        print("Cannot run RyzenAdj because your computer is missing DirectHW.kext or \ndebug=0x144 or SIP is not SET yet")
        input("Press Enter to continue...")
        return
    cfg = ConfigParser()
    time = cfg.get('User', 'Time', fallback='10')
    cfg.read(CONFIG_PATH)
    password = cfg.get('User', 'Password', fallback='')
    if args == 'Custom':
        custom_args = cfg.get('User', 'CustomArgs', fallback='')
        command = ["sudo", "-S", "Assets/ryzenadj"] + custom_args.split()
    else:
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
        time.sleep(time)
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        logging.info(f"Script will be reapplied every {time} seconds")
        logging.info("Press B then Enter to go back to the main menu")
        logging.info("------ RyzenAdj Log ------")
    thread.join()

def info():
    while True:
        about_menu()
        choice = input("Option: ")
        if choice == "1":
            webbrowser.open("https://www.github.com/AppleOSX/UXTU4Mac")
        elif choice == "2":
            clr_print_logo()
            changelog = get_changelog()
            logging.info(
                f"Changelog for the latest version ({get_latest_ver}):\n{changelog}"
            )
            input("Press Enter to continue...")
        elif choice.lower() == "f":
            run_updater()
        elif choice.lower() == "t":
            tester_list()
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid Option.")
            input("Press Enter to continue...")

def tester_list():
    clr_print_logo()
    logging.info("Special thanks to our tester:")
    logging.info("")
    logging.info(" - GorouFlex for AMD Ryzen 5 4500U (Renoir)")
    logging.info(" - nlqanh524 for AMD Ryzen 5 5500U (Lucienne)")
    logging.info("")
    input("Press Enter to continue...")

def check_fip_integrity():
    hash_file_url = 'https://raw.githubusercontent.com/AppleOSX/UXTU4Mac/master/Hash.txt'
    try:
        with urllib.request.urlopen(hash_file_url) as response:
            expected_hash = response.read().decode().strip()
    except urllib.error.URLError:
        clr_print_logo()
        logging.error(f"File Integrity Protection: {hash_file_url} not found. Exiting...")
        sys.exit()
    with open(__file__, 'rb') as file:
        file_content = file.read()
    current_hash = hashlib.sha256(file_content).hexdigest()
    if current_hash != expected_hash:
        clr_print_logo()
        logging.error("File Integrity Protection: File has been modified! Exiting...")
        sys.exit()
    else:
        logging.info("File Integrity Protection: File integrity verified.")

def settings():
    while True:
      setting_menu()
      settings_choice = input("Option: ")
      if settings_choice == "1":
         preset_cfg()
      elif settings_choice == "2":
         fip_cfg()
      elif settings_choice == "3":
         cfu_cfg()
      elif settings_choice == "4":
         login_cfg()
      elif settings_choice == "5":
         pass_cfg()
      elif settings_choice == "6":
         sleep_cfg() 
      elif settings_choice == "b":
         break
      else:
       logging.info("Invalid Option.")
       input("Press Enter to continue...")
       
def main():
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    if cfg.get('User', 'cfu', fallback = '1') == '1':
         check_updates()
    else:
        clr_print_logo()
        logging.info("Skipping CFU...")
    fip_enabled = cfg.get('User', 'FIP', fallback='0') == '1'
    if fip_enabled:
        check_fip_integrity()
    check_cfg_integrity()
    time = cfg.get('User', 'Time', fallback='10')
    if user_mode := read_cfg():
        clr_print_logo()
        logging.info(f"Using mode: {user_mode}")
        logging.info(f"Script will be reapplied every {time} seconds")
        logging.info("Press B then Enter to go back to the main menu")
        logging.info("------ RyzenAdj Log ------")
        if user_mode in PRESETS:
          run_cmd(PRESETS[user_mode], user_mode)
        else:
          run_cmd(user_mode, user_mode)
    while True:                
        main_menu()
        choice = input("Option: ")
        if choice == "1":
            clr_print_logo()
            logging.info("Apply Preset:")
            logging.info("1. Load saved settings from config file")
            logging.info("2. Load from available premade preset")
            logging.info("3. Custom preset (Beta)")
            logging.info("")
            logging.info("B. Back")
            preset_choice = input("Option: ")
            if preset_choice == "1":
                if user_mode := read_cfg():
                    clr_print_logo()
                    logging.info(f"Using mode: {user_mode}")
                    logging.info(f"Script will be reapplied every {time} seconds")
                    logging.info("Press B then Enter to go back to the main menu")
                    logging.info("------ RyzenAdj Log ------")
                    if user_mode in PRESETS:
                      run_cmd(PRESETS[user_mode], user_mode)
                    else:
                     run_cmd(user_mode, user_mode)
                else:
                    logging.info("Config file is missing or invalid. Please run the script again.")
                    input("Press Enter to continue...")
            elif preset_choice == "2":
                clr_print_logo()
                logging.info("Select a premade preset:")
                for i, mode in enumerate(PRESETS, start=1):
                  logging.info(f"{i}. {mode}")
                preset_number = input("Choose a preset by entering the number: ")
                try:
                  preset_number = int(preset_number)
                  if 1 <= preset_number <= len(PRESETS):
                     selected_preset = list(PRESETS.keys())[preset_number - 1]
                     clr_print_logo()
                     user_mode = selected_preset
                     logging.info(f"Using mode: {user_mode}")
                     logging.info(f"Script will be reapplied every {time} seconds")
                     logging.info("Press B then Enter to go back to the main menu")
                     logging.info("------ RyzenAdj Log ------")
                     run_cmd(PRESETS[user_mode], user_mode)
                  else:
                    logging.info("Invalid Option.")
                    input("Press Enter to continue...")
                except ValueError:
                 logging.info("Invalid input. Please enter a number.")
            elif preset_choice == "3":
              custom_args = input("Custom arguments (preset): ")
              clr_print_logo()
              user_mode = "Custom"
              logging.info(f"Using mode: {user_mode}")
              logging.info(f"Script will be reapplied every {time} seconds")
              logging.info("Press B then Enter to go back to the main menu")
              logging.info("------ RyzenAdj Log ------")
              run_cmd(custom_args, user_mode)
            elif preset_choice.lower() == "b":
                  continue
            else:
                logging.info("Invalid Option.")
        elif choice == "2":
             settings()
        elif choice.lower() == "i":
           install_kext_menu()
        elif choice.lower() == "h":
            print_system_info()
        elif choice.lower() == "a":
            info()
        elif choice.lower() == "q":
            clr_print_logo()
            logging.info("Quitting...")
            sys.exit()
        else:
            logging.info("Invalid Option.")
            input("Press Enter to continue...")
                
if __name__ == "__main__":
    main()
