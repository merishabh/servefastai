import json
import os
import shutil
import subprocess
import json
import sys
import dill
import torch
from pathlib import Path
from typing import List

CONFIG_DIR = Path.home()/'.servefastai'
CONFIG_FNAME = 'config.json'

class ServeFastAI():

    DEPLOY_MODES = ["heroku", "gcp", "local"]

    def __init__(self, deploy_mode, deploy_dir="deploy", model_weights_path=None, output_classes=[], image_size=299, model_arch=None):
        """
        
        """
        self.deploy_dir = deploy_dir
        self.model_cfg_name = "model_cfg.json"
        if deploy_mode in self.DEPLOY_MODES:
            self.deploy_mode = self.DEPLOY_MODES.index(deploy_mode)
        else:
            print("Please choose heroku, gcp or local for deployment")
            return

        with open(CONFIG_DIR/CONFIG_FNAME) as f:
            self.config_file_dict = json.load(f)

        base_path = os.path.dirname(os.path.realpath(__file__))
        response = 'y'
        if os.path.exists(deploy_dir):
            response = input("Do you want to override the existing files?(y/n)")
        else:
            os.makedirs(deploy_dir)

        if response.lower() != 'y':
            print ("Not Overriding the deploy files")
            return

        shutil.rmtree(deploy_dir)
        os.makedirs(deploy_dir)
        # TODO: Replace os.path with Path()

        
        if not os.path.exists(os.path.join(deploy_dir, "templates")):
            shutil.copytree(os.path.join(base_path, "templates"), os.path.join(deploy_dir, "templates"))
        # TODO: Add support for gcp heroku
        shutil.copyfile(os.path.join(base_path,"dockerfiles", "Dockerfile_heroku"), os.path.join(deploy_dir, "Dockerfile"))
        shutil.copyfile(os.path.join(base_path, "server.py"), os.path.join(deploy_dir, "server.py"))
        
        # Export learn model
        shutil.copyfile(model_weights_path, os.path.join(deploy_dir, "model.pth"))
        
        # Save model load configurations
        model_cfg = {
            "model_weights_path": "model.pth",
            "output_classes": output_classes,
            "image_size": image_size,
            "model_arch": model_arch
        }
        with open(os.path.join(deploy_dir, self.model_cfg_name), "w") as f:
            f.write(json.dumps(model_cfg))

    def test_local(self):
       # TODO: Handle exit condition gracefully by forking the process
       subprocess.call('cd ' + self.deploy_dir + ' && python server.py', shell=True)

    def run_subprocess(self, command):
        subp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout , stderr = subp.communicate()
        print (stdout, stderr)
        return stdout.decode("utf-8").strip(), stderr.decode("utf-8").strip()

    def deploy(self, app_name):
        if self.deploy_mode == 0:
            self._deploy_heroku(app_name)
        elif self.deploy_mode == 1:
            self._deploy_gcp()

    def _deploy_heroku(self, app_name):
        """
        """
        #TODO: Apt get install snapd, Heroku
        username = config_file_dict["heroku"]["username"]
        app = app_name
        is_heroku_login = self.rub_subprocess('heroku auth:token')
        heroku_login_result = self.run_subprocess('heroku container:login')
        if heroku_login_result[0].lower() != 'login succeeded':
            return
        docker_login_result = self.run_subprocess('docker login --username=' + username +' --password=$(heroku auth:token)     registry.heroku.com')
               
        #TODO: check docker login result 

        available_apps_result = self.run_subprocess('heroku apps')
        
        if app_name not in available_apps_result[0].split(' ')[2].splitlines():
            create_app = self.run_subprocess('heroku create ' + app_name)

        heroku_container_push = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:push web -a ' + app_name)
        #TODO: Parse Container build results.
        heroku_container_release = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:release web -a ' + app_name)

    def _deploy_gcp(self):
        #TODO: installing gcloud
        #TODO: the user should login first to the gcloud.
        
        google_cloud_login = self.run_subprocess('gcloud auth login --no-launch-browser')
        

        
        
        
        
        