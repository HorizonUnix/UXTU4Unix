import os
import urllib.request
import zipfile
import shutil
import subprocess

def update():
    url = "https://github.com/AppleOSX/UXTU4Mac/releases/latest/download/UXTU4Mac.zip"
    script_dir = os.path.dirname(os.path.realpath(__file__))
    current_dir = os.path.dirname(os.path.dirname(script_dir))
    current_folder = os.path.join(current_dir, "UXTU4Mac")
    new_folder = os.path.join(current_dir, "UXTU4Mac_new")
    urllib.request.urlretrieve(url, os.path.join(current_dir, "UXTU4Mac.zip"))
    with zipfile.ZipFile(os.path.join(current_dir, "UXTU4Mac.zip"), 'r') as zip_ref:
        zip_ref.extractall(new_folder)
    
    shutil.rmtree(current_folder)
    inner_folder = os.path.join(new_folder, "UXTU4Mac")
    shutil.move(inner_folder, current_dir)
    shutil.rmtree(new_folder)

    subprocess.call(['chmod', '+x', os.path.join(current_dir, "UXTU4Mac", "UXTU4Mac.command")])
    subprocess.call(['chmod', '+x', os.path.join(current_dir, "UXTU4Mac", "Assets", "ryzenadj")])

if __name__ == "__main__":
    update()
