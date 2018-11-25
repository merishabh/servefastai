import json
import os
import shutil
import subprocess
import json
import sys
import dill
import torch
import time
from pathlib import Path
from typing import List
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials



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
        with open(os.path.join(deploy_dir, self.model_cfg_name), "w") as f:
            f.write(json.dumps(model_cfg))

    def test_local(self):
       # TODO: Handle exit condition gracefully by forking the process
       subprocess.call('cd ' + self.deploy_dir + ' && python server.py', shell=True)

    def run_subprocess(self, command):
        subp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout , stderr = subp.communicate()
        return stdout.decode("utf-8").strip(), stderr.decode("utf-8").strip()

    def deploy(self):
        if self.deploy_mode == 0:
            self._deploy_heroku()
        elif self.deploy_mode == 1:
            self._deploy_gcp()

    def _deploy_heroku(self):
        """
        """
        #TODO: Apt get install snapd, Heroku
        username = self.config_file_dict["heroku"]["username"]
        app_name = self.config_file_dict["heroku"]["app-name"]
        print ("Fetching the auth token")
        is_heroku_login = self.run_subprocess('heroku auth:token')
        print ("Logging into Heroku")
        heroku_login_result = self.run_subprocess('heroku container:login')
        if heroku_login_result[0].lower() != 'login succeeded':
            print (heroku_login_result[1])
            return
        print ("Logging into Docker")
        docker_login_result = self.run_subprocess('docker login --username=' + username +' --password=$(heroku auth:token)     registry.heroku.com')
               
        #TODO: check docker login result 

        available_apps_result = self.run_subprocess('heroku apps')
        
        if app_name not in available_apps_result[0].split(' ')[2].splitlines():
            print ("Creating the app")
            create_app = self.run_subprocess('heroku create ' + app_name)
        else:
            print ("App is already present")
        print ("Pushing the image to heroku repository")
        heroku_container_push = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:push web -a ' + app_name)
        #TODO: Parse Container build results.
        print ("Releasing the image")
        heroku_container_release = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:release web -a ' + app_name)
    
    def _list_instances(self, compute, project, zone):
        result = compute.instances().list(project=project, zone=zone).execute()
        return result['items']
    
    def _wait_for_operation(self, compute, project, zone, operation):
        print('Waiting for operation to finish...')
        while True:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation).execute()

            if result['status'] == 'DONE':
                print("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)
        
    def _create_instance(self, compute, project_id, image_project, image_family, zone, instance_name, machine_type):
        """
        """
        image_response = compute.images().getFromFamily(project=image_project, family=image_family).execute()
        source_disk_image = image_response['selfLink']
        machine_type = "zones/%s/machineTypes/%s" % (zone, machine_type)
        config = {
        'name': instance_name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }]
      }
        compute.instances().insert(
        project=project_id,
        zone=zone,
        body=config).execute()
        
    def _deploy_gcp(self):
        #TODO: Readme for installing gcloud
        #TODO: Readme for asking user to login
        #TODO: Delete Instance (to confirm)
        credentials = GoogleCredentials.get_application_default()
        compute = discovery.build('compute', 'v1', credentials=credentials)
        project_id = self.config_file_dict["gcp"]["project_id"]
        image_project = self.config_file_dict["gcp"]["image_project"]
        image_family = self.config_file_dict["gcp"]["image_family"]
        zone = self.config_file_dict["gcp"]["zone"]
        instance_name = self.config_file_dict["gcp"]["instance_name"]
        machine_type = "custom-" + self.config_file_dict["gcp"]["number_of_cpus"] + "-" + self.config_file_dict["gcp"]["amount_of_memory_per_cpu(MB)"]
        instances_items = self._list_instances(compute, project_id, zone)
        
        instance_list = [{"name": i["name"], "status": i["status"]} for i in instances_items]
        is_instance_exists = False
        instance_status = ''
        for instance in instance_list:
            if instance['name'] == instance_name:
                is_instance_exists = True
                instance_status = instance['status']
                break
                
        if not is_instance_exists:
            operation = self._create_instance(compute, project_id, image_project, image_family, zone, instance_name, machine_type)
            self._wait_for_operation(compute, project_id, zone, operation['name'])
        else:
            if instance_status != 'RUNNING':
                print ("Instance is not running. Restarting the instance")
                request = compute.instances().start(project=project_id, zone=zone, instance=instance_name)
                response = request.execute()
                self._wait_for_operation(compute, project_id, zone, response['name'])
            else:
                print ("Instance is already up and running. Moving forward to Deployment")
               
        print("Copying Files from one instance to another")
        copy_deploy_to_instance = self.run_subprocess("gcloud compute scp --recurse %s root@%s:%s --zone %s" %(self.deploy_dir, instance_name, Path.home(), zone))
        if copy_deploy_to_instance[0]:
            print (copy_deploy_to_instance[0])
        print("Installing docker on the remote machine if it is not already installed")
        install_docker = self.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && sudo chmod +x install_docker.sh && ./install_docker.sh"' % (instance_name, zone, Path.home()))
        if install_docker[0]:
            print ("hey " + install_docker[0])
        print("Building image on the remote machine")
        build_image = self.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && docker build --build-arg arg_port=5000 -t servefastai-image ."' % (instance_name, zone, Path.home()))
        if build_image[0]:
            print ("hey " + build_image[0])
        print("Running image on the remote machine")
        run_container = self.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && sudo chmod +x run_image.sh && ./run_image.sh"' % (instance_name, zone, Path.home()))
        if run_container[1]:
            print ("Error: " + run_container[1])
        else:
            print ("Output: " + run_container[0])