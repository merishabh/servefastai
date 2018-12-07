import os
import json
import shutil
from pathlib import Path
import sqlite3
import subprocess

CONFIG_DIR = Path.home()/'.servefastai'
DB_NAME = 'servefast.db'
HOST_ADD_WARNING = 'Failed to add the host to the list of known hosts (' + os.path.join(Path.home(), '.ssh/google_compute_known_hosts') + ').'

DEPLOY_MODES = ["heroku", "gcp", "local"]
 
def get_sqlite_connection():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    conn = sqlite3.connect(os.path.join(CONFIG_DIR, DB_NAME))
    return conn
    
def _code_deploy(deploy_mode, deploy_dir="deploy", model_weights_path=None, output_classes=[], image_size=299, model_arch=None):
    """
    
    """

    base_path = os.path.dirname(os.path.realpath(__file__))
    response = 'y'
    if os.path.exists(deploy_dir):
        response = input("Do you want to override the existing files?(y/n)")
    else:
        os.makedirs(deploy_dir)

    if response.lower() != 'y':
        print ("Not Overriding the deploy folder files")
        return

    shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    # TODO: Replace os.path with Path()


    if not os.path.exists(os.path.join(deploy_dir, "templates")):
        shutil.copytree(os.path.join(base_path, "templates"), os.path.join(deploy_dir, "templates"))
    # TODO: Add support for gcp heroku
    if deploy_mode == 0:          
        shutil.copyfile(os.path.join(base_path,"dockerfiles", "Dockerfile_heroku"), os.path.join(deploy_dir, "Dockerfile"))
    elif deploy_mode == 1:
        shutil.copyfile(os.path.join(base_path,"dockerfiles", "Dockerfile_gcp"), os.path.join(deploy_dir, "Dockerfile"))
    shutil.copyfile(os.path.join(base_path, "server.py"), os.path.join(deploy_dir, "server.py"))
    shutil.copyfile(os.path.join(base_path, "install_docker.sh"), os.path.join(deploy_dir, "install_docker.sh"))
    shutil.copyfile(os.path.join(base_path, "run_image.sh"), os.path.join(deploy_dir, "run_image.sh"))
    # Export learn model
    shutil.copyfile(model_weights_path, os.path.join(deploy_dir, "model.pth"))

    # Save model load configurations
    model_cfg = {
        "model_weights_path": "model.pth",
        "output_classes": output_classes,
        "image_size": image_size,
        "model_arch": model_arch
    }
    with open(os.path.join(deploy_dir, "model_cfg.json"), "w") as f:
        f.write(json.dumps(model_cfg))
    print ("Deploy Folder files are overridden")

def run_subprocess(command):
    subp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout , stderr = subp.communicate()
    return stdout.decode("utf-8").strip(), stderr.decode("utf-8").strip()