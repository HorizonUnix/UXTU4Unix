import os, urllib.request, zipfile, shutil, subprocess
 
def update():
    url = "https://github.com/AppleOSX/UXTU4Mac/releases/latest/download/UXTU4Mac.zip"
    script_dir = os.path.dirname(os.path.realpath(__file__))
    current_dir = os.path.dirname(os.path.dirname(script_dir))
    current_folder = os.path.join(current_dir, "UXTU4Mac")
    new_folder = os.path.join(current_dir, "UXTU4Mac_new")
    config_file = os.path.join(current_folder, "Assets", "config.ini")
    backup_config = os.path.join(current_dir, "config.ini.bak")
    zip_file_path = os.path.join(current_dir, "UXTU4Mac.zip")
    if os.path.exists(config_file):
        shutil.copy2(config_file, backup_config)
    urllib.request.urlretrieve(url, zip_file_path)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(new_folder)
    shutil.rmtree(current_folder)
    inner_folder = os.path.join(new_folder, "UXTU4Mac")
    shutil.move(inner_folder, current_dir)
    shutil.rmtree(new_folder)
    subprocess.call(['chmod', '+x', os.path.join(current_dir, "UXTU4Mac", "UXTU4Mac.command")])
    subprocess.call(['chmod', '+x', os.path.join(current_dir, "UXTU4Mac", "Assets", "ryzenadj")])
    if os.path.exists(backup_config):
        shutil.move(backup_config, config_file)
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)

if __name__ == "__main__":
    update()
