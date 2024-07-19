import os
import time
import subprocess
import getpass
import webbrowser
import logging
import sys
import binascii
import urllib.request
import json
import select
from configparser import ConfigParser

# Constants
LOCAL_VERSION = "0.3.03"
LATEST_VERSION_URL = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/HorizonUnix/UXTU4Unix/releases/latest"
current_dir = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(current_dir, 'Assets', 'config.ini')

# Setup Logging
log_dir = os.path.join(current_dir, 'Logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'UXTU4Unix.log'),
    filemode='w',
    encoding='utf-8',
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
logging.getLogger().addHandler(logging.StreamHandler())

# Load Configurations
cfg = ConfigParser()
cfg.read(CONFIG_PATH)

ryzen_family = [
    "Unknown", "SummitRidge", "PinnacleRidge", "RavenRidge", "Dali", "Pollock",
    "Picasso", "FireFlight", "Matisse", "Renoir", "Lucienne", "VanGogh", "Mendocino",
    "Vermeer", "Cezanne_Barcelo", "Rembrandt", "Raphael", "DragonRange", "PhoenixPoint",
    "PhoenixPoint2", "HawkPoint", "SonomaValley", "GraniteRidge", "FireRange",
    "StrixPoint", "StrixPoint2", "Sarlak"
]

def clear():
    subprocess.call('clear', shell=True)
    logging.info(r"""
   _   ___  _______ _   _ _ _  _   _      _     
  | | | \ \/ /_   _| | | | | || | | |_ _ (_)_ __
  | |_| |>  <  | | | |_| |_  _| |_| | ' \| \ \ /
   \___//_/\_\ |_|  \___/  |_| \___/|_||_|_/_\_\ """)
    logging.info("")
    cpu = cfg.get('Info', 'CPU', fallback='')
    family = cfg.get('Info', 'Family', fallback='')
    if cpu and family:
       logging.info(f'  {cpu} ({family})')
    if cfg.get('Settings', 'Debug', fallback='0') == '1':
        logging.info(f"  Loaded: {cfg.get('User', 'Preset',fallback = '')}")
    logging.info(f"  Version: {LOCAL_VERSION} by HorizonUnix (Linux Edition)")
    logging.info("")

def get_hardware_info(command, use_sudo=False):
    password = cfg.get('User', 'Password', fallback='')
    if use_sudo:
        command = f"echo '{password}' | sudo -S {command}"
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8').strip()

def get_codename():
    cpu = cfg.get('Info', 'CPU')
    signature = cfg.get('Info', 'Signature')
    words = signature.split(' ')
    family_index = words.index("Family") + 1
    model_index = words.index("Model") + 1
    stepping_index = words.index("Stepping") + 1
    cpu_family = int(words[family_index].rstrip(','))
    cpu_model = int(words[model_index].rstrip(','))
    cpu_stepping = int(words[stepping_index].rstrip(','))

    architecture = 'Unknown'
    family = 'Unknown'

    if cpu == 'Intel':
        architecture = 'Intel'
        family = 'Intel'
    elif cpu_family == 23:
        architecture = 'Zen 1 - Zen 2'
        if cpu_model == 1:
            family = 'SummitRidge'
        elif cpu_model == 8:
            family = 'PinnacleRidge'
        elif cpu_model in {17, 18}:
            family = 'RavenRidge'
        elif cpu_model == 24:
            family = 'Picasso'
        elif cpu_model == 32:
            family = 'Pollock' if '15e' in cpu or '15Ce' in cpu or '20e' in cpu else 'Dali'
        elif cpu_model == 80:
            family = 'FireFlight'
        elif cpu_model == 96:
            family = 'Renoir'
        elif cpu_model == 104:
            family = 'Lucienne'
        elif cpu_model == 113:
            family = 'Matisse'
        elif cpu_model == 144:
            family = 'VanGogh'
        elif cpu_model == 160:
            family = 'Mendocino'
    elif cpu_family == 25:
        architecture = 'Zen 3 - Zen 4'
        if cpu_model == 33:
            family = 'Vermeer'
        elif cpu_model in {63, 68}:
            family = 'Rembrandt'
        elif cpu_model == 80:
            family = 'Cezanne_Barcelo'
        elif cpu_model == 97:
            family = 'DragonRange' if 'HX' in cpu else 'Raphael'
        elif cpu_model == 116:
            family = 'PhoenixPoint'
        elif cpu_model == 120:
            family = 'PhoenixPoint2'
        elif cpu_model == 117:
            family = 'HawkPoint'
    elif cpu_family == 26:
        architecture = 'Zen 5 - Zen 6'
        if cpu_model == 32:
            family = 'StrixPoint'
        else:
            family = 'GraniteRidge'

    cfg.set('Info', 'Architecture', architecture)
    cfg.set('Info', 'Family', family)

    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)

    if family in {'SummitRidge', 'PinnacleRidge', 'Matisse', 'Vermeer', 'Raphael', 'GraniteRidge'}:
        cfg.set('Info', 'Type', 'Amd_Desktop_Cpu')
    elif architecture == 'Intel':
        cfg.set('Info', 'Type', 'Intel')
    elif architecture == 'Unknown':
        cfg.set('Info', 'Type', 'Unknown')

    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)

def get_presets():
    cpu_family = cfg.get('Info', 'Family')
    cpu_model = cfg.get('Info', 'CPU').replace("AMD", "").replace("with", "").replace("Mobile", "").replace("Ryzen", "").replace("Radeon", "").replace("Graphics", "").replace("Vega", "").replace("Gfx", "")
    cpu_type = cfg.get('Info', 'Type')
    presets_module = None

    if cpu_type == 'Amd_Apu':
        if ryzen_family.index(cpu_family) < ryzen_family.index("Matisse"):
            if any(x in cpu_model for x in ["U", "e", "Ce"]):
                presets_module = "AMDAPUPreMatisse_U_e_Ce"
            elif "H" in cpu_model:
                presets_module = "AMDAPUPreMatisse_H"
            elif "GE" in cpu_model:
                presets_module = "AMDAPUPreMatisse_GE"
            elif "G" in cpu_model:
                presets_module = "AMDAPUPreMatisse_G"
            else:
                presets_module = "AMDCPU"
        elif ryzen_family.index(cpu_family) > ryzen_family.index("Matisse"):
            if "U" in cpu_model:
                presets_module = "AMDAPUPostMatisse_U"
            elif "HX" in cpu_model:
                presets_module = "AMDAPUPostMatisse_HX"
            elif "HS" in cpu_model:
                presets_module = "AMDAPUPostMatisse_HS"
            elif "H" in cpu_model:
                presets_module = "AMDAPUPostMatisse_H"
            elif "GE" in cpu_model:
                presets_module = "AMDAPUPostMatisse_GE"
            elif "G" in cpu_model:
                presets_module = "AMDAPUPostMatisse_G"
            else:
                presets_module = "AMDCPU"
    elif cpu_type == 'Amd_Desktop_Cpu':
        if ryzen_family.index(cpu_family) < ryzen_family.index("Raphael"):
            if "E" in cpu_model:
                presets_module = "AMDCPUPreRaphael_E"
            elif "X3D" in cpu_model:
                presets_module = "AMDCPUPreRaphael_X3D"
            elif "X" in cpu_model and "9" in cpu_model:
                presets_module = "AMDCPUPreRaphael_X9"
            elif "X" in cpu_model:
                presets_module = "AMDCPUPreRaphael_X"
            else:
                presets_module = "AMDCPUPreRaphael"
        else:
            if "E" in cpu_model:
                presets_module = "AMDCPU_E"
            elif "X3D" in cpu_model:
                presets_module = "AMDCPU_X3D"
            elif "X" in cpu_model and "9" in cpu_model:
                presets_module = "AMDCPU_X9"
            else:
                presets_module = "AMDCPU"
    else:
        presets_module = "AMDCPU"

    module = __import__(f"Assets.Presets.{presets_module}", fromlist=['PRESETS'])
    cfg.set('User', 'Preset', f"Assets.Presets.{presets_module}")
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    return module.PRESETS

def hardware_info():
    clear()
    logging.info("Processor Information:")
    logging.info(f" - Processor: {cfg.get('Info', 'CPU')}")
    cpu_family = cfg.get('Info', 'Family')
    smu_version = get_hardware_info(f"{current_dir}/Assets/ryzenadj -i | grep 'SMU BIOS Interface Version'", use_sudo=True).strip()
    if cpu_family:
        logging.info(f" - Codename: {cpu_family}")
    if smu_version:
        logging.info(f" - {smu_version}")
    logging.info(f" - Architecture: {cfg.get('Info', 'Architecture')}")
    logging.info(f" - Type: {cfg.get('Info', 'Type')}")
    logging.info(f" - Cores: {cfg.get('Info', 'Core Count')}")
    logging.info(f" - Threads: {cfg.get('Info', 'Thread Count')}")
    logging.info(f" - Max speed: {cfg.get('Info', 'Max Speed')}")
    logging.info(f" - Current speed: {cfg.get('Info', 'Current Speed')}")
    logging.info("")
    input("Press Enter to continue...")

def welcome_tutorial():
    if not cfg.has_section('User'):
        cfg.add_section('User')
    if not cfg.has_section('Settings'):
        cfg.add_section('Settings')
    if not cfg.has_section('Info'):
        cfg.add_section('Info')
    clear()
    logging.info("--------------- Welcome to UXTU4Unix ---------------")
    logging.info("Designed for AMD Zen-based processors on macOS/Linux")
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
    cfg.set('User', 'Password', password)
    cfg.set('Settings', 'Time', '30')
    cfg.set('Settings', 'SoftwareUpdate', '1')
    cfg.set('Settings', 'ReApply', '0')
    cfg.set('Settings', 'ApplyOnStart', '1')
    cfg.set('Settings', 'DynamicMode', '0')
    cfg.set('Settings', 'Debug', '1')
    cfg.set('Info', 'CPU', get_hardware_info("dmidecode -t processor | grep 'Version' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Signature', get_hardware_info("dmidecode -t processor | grep 'Signature' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Voltage', get_hardware_info("dmidecode -t processor | grep 'Voltage' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Max Speed', get_hardware_info("dmidecode -t processor | grep 'Max Speed' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Current Speed', get_hardware_info("dmidecode -t processor | grep 'Current Speed' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Core Count', get_hardware_info("dmidecode -t processor | grep 'Core Count' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Core Enabled', get_hardware_info("dmidecode -t processor | grep 'Core Enabled' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    cfg.set('Info', 'Thread Count', get_hardware_info("dmidecode -t processor | grep 'Thread Count' | awk -F': ' '{print $2}'", use_sudo=True).strip())
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    get_codename()
    preset_cfg()
    clear()

def settings():
    options = {
        "1": preset_cfg,
        "2": sleep_cfg,
        "3": dynamic_cfg,
        "4": reapply_cfg,
        "5": applystart_cfg,
        "6": cfu_cfg,
        "7": pass_cfg,
        "8": debug_cfg,
        "r": reset,
        "b": "break"
    }
    while True:
        clear()
        logging.info("--------------- Settings ---------------")
        logging.info("1. Preset\n2. Sleep time")
        logging.info("3. Dynamic mode\n4. Auto reapply")
        logging.info("5. Apply on start")
        logging.info("6. Software update")
        logging.info("7. Sudo password")
        logging.info("8. Debug\n")
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

def applystart_cfg():
    while True:
        clear()
        logging.info("--------------- Apply on start ---------------")
        logging.info("(Apply preset when start)")
        start_enabled = cfg.get('Settings', 'ApplyOnStart', fallback='1') == '1'
        logging.info("Status: Enabled" if start_enabled else "Status: Disabled")
        logging.info("\n1. Enable Apply on start\n2. Disable Apply on start\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'ApplyOnStart', '1')
        elif choice == "2":
            cfg.set('Settings', 'ApplyOnStart', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def debug_cfg():
    while True:
        clear()
        logging.info("--------------- Debug ---------------")
        logging.info("(Display some process information)")
        debug_enabled = cfg.get('Settings', 'Debug', fallback='1') == '1'
        logging.info("Status: Enabled" if debug_enabled else "Status: Disabled")
        logging.info("\n1. Enable Debug\n2. Disable Debug\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'Debug', '1')
        elif choice == "2":
            cfg.set('Settings', 'Debug', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def reapply_cfg():
    while True:
        clear()
        logging.info("--------------- Auto reapply ---------------")
        logging.info("(Automatic reapply preset)")
        reapply_enabled = cfg.get('Settings', 'ReApply', fallback='0') == '1'
        logging.info("Status: Enabled" if reapply_enabled else "Status: Disabled")
        logging.info("\n1. Enable Auto reapply\n2. Disable Auto reapply\n\nB. Back")
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

def dynamic_cfg():
    while True:
        clear()
        dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'
        logging.info("--------------- Dynamic mode ---------------")
        logging.info("(Automatic switch preset based on your battery usage)")
        logging.info("Status: Enabled" if dm_enabled else "Status: Disabled")
        logging.info("\n1. Enable Dynamic Mode\n2. Disable Dynamic Mode\n\nB. Back")
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
        logging.info("\n1. Change\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            set_time = input("Enter your auto reapply time (Default is 30): ")
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
        logging.info("\n1. Change password\n\nB. Back")
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

def cfu_cfg():
    while True:
        clear()
        cfu_enabled = cfg.get('Settings', 'SoftwareUpdate', fallback='1') == '1'
        logging.info("--------------- Software update ---------------")
        logging.info(f"Status: {'Enabled' if cfu_enabled else 'Disabled'}")
        logging.info("\n1. Enable Software update\n2. Disable Software update\n\nB. Back")
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
    PRESETS = get_presets()
    while True:
        clear()
        logging.info("--------------- Preset ---------------")
        for i, (preset_name, preset_value) in enumerate(PRESETS.items(), start=1):
            logging.info(f"{i}. {preset_name}")
        logging.info("\nD. Dynamic Mode\nC. Custom (Beta)\nB. Back")
        logging.info("We recommend using the Dynamic Mode for normal tasks and better power management")
        choice = input("Option: ").lower().strip()
        if choice == 'c':
            custom_args = input("Enter your custom arguments: ")
            cfg.set('User', 'Mode', 'Custom')
            cfg.set('User', 'CustomArgs', custom_args)
            if cfg.get('Settings', 'DynamicMode', fallback='0') == '1':
                cfg.set('Settings', 'DynamicMode', '0')
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
                if cfg.get('Settings', 'DynamicMode', fallback='0') == '1':
                    cfg.set('Settings', 'DynamicMode', '0')
                logging.info("Set preset successfully!")
                input("Press Enter to continue...")
                with open(CONFIG_PATH, 'w') as config_file:
                    cfg.write(config_file)
                break
            except ValueError:
                logging.info("Invalid option.")
                input("Press Enter to continue")

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
    required_keys_settings = ['time', 'dynamicmode', 'reapply', 'applyonstart', 'softwareupdate', 'debug']
    required_keys_info = ['cpu', 'signature', 'voltage', 'max speed', 'current speed', 'core count', 'core enabled', 'thread count', 'architecture', 'family', 'type']
    if not cfg.has_section('User') or not cfg.has_section('Settings') or not cfg.has_section('Info') or \
    any(key not in cfg['User'] for key in required_keys_user) or \
    any(key not in cfg['Settings'] for key in required_keys_settings) or \
    any(key not in cfg['Info'] for key in required_keys_info):
        reset()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def get_changelog():
    request = urllib.request.Request(GITHUB_API_URL)
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data['body']

def updater():
    while True:
        clear()
        changelog = get_changelog()
        logging.info("--------------- UXTU4Unix Software Update ---------------")
        logging.info("A new update is available!")
        logging.info(f"Changelog for the latest version ({get_latest_ver()}):\n{changelog}")
        logging.info("Do you want to update? (y/n): ")
        choice = input("Option: ").lower().strip()
        if choice == "y":
            subprocess.run(["python3", os.path.join(current_dir, 'Assets', 'SU.py')])
            logging.info("Updating...")
            logging.info("Update complete. Restarting the application, please close this window...")
            break
        elif choice == "n":
            logging.info("Skipping update...")
            break
        else:
            logging.info("Invalid option.")
    raise SystemExit

def check_updates():
    clear()
    max_retries = 10
    skip_update_check = False
    for i in range(max_retries):
        try:
            latest_version = get_latest_ver()
        except Exception as e:
            if i < max_retries - 1:
                logging.info(f"Failed to fetch latest version. Retrying {i+1}/{max_retries}... {str(e)}")
                time.sleep(5)
            else:
                clear()
                logging.info("Failed to fetch latest version")
                result = input("Do you want to skip the check for updates? (y/n): ").lower().strip()
                if result == "y":
                    skip_update_check = True
                else:
                    logging.info("Quitting...")
                    raise SystemExit
    if not skip_update_check:
        if LOCAL_VERSION < latest_version:
            updater()
        elif LOCAL_VERSION > latest_version:
            clear()
            logging.info("Welcome to the UXTU4Unix Beta Program")
            logging.info("This beta build may not work as expected and is only for testing purposes!")
            result = input("Do you want to continue (y/n): ").lower().strip()
            if result == "y":
                pass
            else:
                logging.info("Quitting...")
                raise SystemExit

def about():
    options = {
        "1": lambda: webbrowser.open("https://www.github.com/HorizonUnix/UXTU4Unix"),
        "f": updater,
        "b": "break",
    }
    while True:
        clear()
        logging.info("About UXTU4Unix")
        logging.info("The New Future Vision Update (3Linux290724)")
        logging.info("----------------------------")
        logging.info("Maintainer: GorouFlex\nCLI: GorouFlex")
        logging.info("GUI: NotchApple1703\nCore: NotchApple1703")
        logging.info("Advisor: NotchApple1703")
        logging.info("dmidecode for macOS: Acidanthera")
        logging.info("Command file for macOS: CorpNewt\nTester: nlqanh524")
        logging.info("----------------------------")
        try:
            logging.info(f"F. Force update to the latest version ({get_latest_ver()})")
        except:
            pass
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
    PRESETS = get_presets()
    clear()
    logging.info("Apply power management settings:")
    logging.info("1. Load saved settings from config file\n2. Load from available premade preset\n\nD. Dynamic Mode\nB. Back")
    preset_choice = input("Option: ").strip()
    if preset_choice == "1":
        user_mode = read_cfg()
        if user_mode in PRESETS:
            apply_smu(PRESETS[user_mode], user_mode)
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
                last_mode = cfg.get('Settings', 'DynamicMode', fallback='0')
                cfg.set('Settings', 'DynamicMode', '0')
                user_mode = selected_preset
                apply_smu(PRESETS[user_mode], user_mode)
                cfg.set('Settings', 'DynamicMode', last_mode)
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
    if cfg.get('Info', 'Type') == "Intel":
        clear()
        logging.info("Sorry, we currently do not support Intel chipsets")
        input("Press Enter to continue...")
        return
    sleep_time = cfg.get('Settings', 'Time', fallback='30')
    password = cfg.get('User', 'Password', fallback='')
    dynamic = cfg.get('Settings', 'DynamicMode', fallback='0')
    last_apply = cfg.get('Settings', 'ReApply', fallback='0')
    PRESETS = get_presets()
    dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'

    if dm_enabled:
        cfg.set('Settings', 'ReApply', '1')

    reapply = cfg.get('Settings', 'ReApply', fallback='0')
    if reapply == '1':
        while True:
            if dynamic == '1':
                battery_status = subprocess.check_output(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"]).decode("utf-8")
                if 'state:               charging' in battery_status:
                    user_mode = 'Extreme'
                elif 'state:               discharging' in battery_status:
                    user_mode = 'Eco'
                else:
                    user_mode = 'Extreme'
            clear()
            if args == 'Custom':
                custom_args = cfg.get('User', 'CustomArgs', fallback='')
                command = ["sudo", "-S", os.path.join(current_dir, 'Assets', 'ryzenadj')] + custom_args.split()
            else:
                args = PRESETS[user_mode]
                command = ["sudo", "-S", os.path.join(current_dir, 'Assets', 'ryzenadj')] + args.split()
            logging.info(f"Using preset: {user_mode}")
            if dm_enabled:
                logging.info("Dynamic mode: Enabled")
            else:
                logging.info("Dynamic mode: Disabled")
            logging.info("Auto reapply: Enabled")
            logging.info(f"Script will check and auto reapply if need every {sleep_time} seconds")
            logging.info("Press B then Enter to go back to the main menu")
            logging.info("--------------- RyzenAdj Log ---------------")
            result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(result.stdout.decode())
            if cfg.get('Settings', 'Debug', fallback='1') == '1':
                if result.stderr:
                    logging.info(f"{result.stderr.decode()}")
            for _ in range(int(float(sleep_time))):
                time.sleep(1)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.lower().strip() == 'b':
                        cfg.set('Settings', 'ReApply', last_apply)
                        return
    else:
        clear()
        if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", os.path.join(current_dir, 'Assets', 'ryzenadj')] + custom_args.split()
        else:
            args = PRESETS[user_mode]
            command = ["sudo", "-S", os.path.join(current_dir, 'Assets', 'ryzenadj')] + args.split()
        logging.info(f"Using preset: {user_mode}")
        logging.info("Auto reapply: Disabled")
        logging.info("--------------- RyzenAdj Log ---------------")
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if cfg.get('Settings', 'Debug', fallback='1') == '1':
            if result.stderr:
                logging.info(f"{result.stderr.decode()}")
        input("Press Enter to continue...")

def main():
    subprocess.run("printf '\\e[8;30;100t'", shell=True)
    check_cfg_integrity()
    PRESETS = get_presets()
    if cfg.get('Settings', 'SoftwareUpdate', fallback='0') == '1':
        check_updates()
    if cfg.get('Settings', 'ApplyOnStart', fallback='1') == '1':
        user_mode = read_cfg()
        if user_mode in PRESETS:
            apply_smu(PRESETS[user_mode], user_mode)
        else:
            apply_smu(user_mode, user_mode)
    while True:
        clear()
        options = {
            "1": preset_menu,
            "2": settings,
            "a": about,
            "h": hardware_info,
            "q": lambda: sys.exit("\nThanks for using UXTU4Unix\nHave a nice day!"),
        }
        logging.info("1. Apply power management settings\n2. Settings")
        logging.info("")
        logging.info("H. Hardware Information")
        logging.info("A. About UXTU4Unix")
        logging.info("Q. Quit")
        choice = input("Option: ").lower().strip()
        if action := options.get(choice):
            action()
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
