import os
import json
import shutil
from pathlib import Path
import sqlite3
import traceback
import time
from servefastai import common_helper
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials


CONFIG_DIR = Path.home()/'.servefastai'
CONFIG_FNAME = 'config.json'
DB_NAME = 'servefast.db'
HOST_ADD_WARNING = 'Failed to add the host to the list of known hosts (' + os.path.join(Path.home(), '.ssh/google_compute_known_hosts') + ').'


def _list_instances(compute, project, zone):
        result = compute.instances().list(project=project, zone=zone).execute() 
        return result['items'] if 'items' in result else [] 
    
def _wait_for_operation(compute, project, zone, operation):
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

def _create_instance(compute, project_id, image_project, image_family, zone, instance_name, machine_type):
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
    return compute.instances().insert(project=project_id, zone=zone, body=config)

def _delete_instance(compute, project, zone, instance):
    request = compute.instances().delete(project=project, zone=zone, instance=instance)
    return request

def _stop_instance(compute, project, zone, instance):
    request = compute.instances().stop(project=project, zone=zone, instance=instance)
    return request

def _start_instance(compute, project, zone, instance):
    request = compute.instances().start(project=project_id, zone=zone, instance=instance_name)
    return request

def deploying_gcp_instance(deploy_dir, instance_name, zone):
    
    print("Copying Files from one instance to another")
    copy_deploy_to_instance = common_helper.run_subprocess("gcloud compute scp --recurse %s root@%s:%s --zone %s" %(deploy_dir, instance_name, Path.home(), zone))
    if copy_deploy_to_instance[1] != HOST_ADD_WARNING:
        print (copy_deploy_to_instance[1])
    
    print("Installing docker on the remote machine if it is not already installed")
    install_docker = common_helper.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && sudo chmod +x install_docker.sh && ./install_docker.sh"' % (instance_name, zone, Path.home()))
    if install_docker[0]:
        print (install_docker[0])
        
    print("Building image on the remote machine")
    build_image = common_helper.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && docker build --build-arg arg_port=5000 -t servefastai-image ."' % (instance_name, zone, Path.home()))
    if build_image[0]:
        print (build_image[0])
    
    print("Running image on the remote machine")
    run_container = common_helper.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && sudo chmod +x run_image.sh && ./run_image.sh"' % (instance_name, zone, Path.home()))
    if run_container[1] != HOST_ADD_WARNING:
        print ("Error: " + run_container[1])
    else:
        print ("Output: " + run_container[0])
    docker_running_status = common_helper.run_subprocess('gcloud compute ssh %s --zone %s --command "cd %s/deploy && docker ps | grep python-server"' % (instance_name, zone, Path.home()))
    if docker_running_status[0]:
        return True
    return False
    
def deploy_gcp(deploy_dir, project_id, instance_name, zone, num_of_cpus, amount_of_memory_per_cpu, image_project="ubuntu-os-cloud", image_family="ubuntu-1604-lts"):
    #TODO: Readme for installing gcloud
    #TODO: Readme for asking user to login
    #TODO: Delete Instance (to confirm)
    is_deployed = False
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    
    machine_type = "custom-" + str(num_of_cpus) + "-" + str(amount_of_memory_per_cpu)
    try:
        instances_items = _list_instances(compute, project_id, zone)
    except HttpError as err:
        print (json.loads(err.content).get('error').get('errors')[0])
        instances_items = []
    instance_list = [{"name": i["name"], "status": i["status"]} for i in instances_items]
    is_instance_exists = False
    instance_status = ''
    for instance in instance_list:
        if instance['name'] == instance_name:
            is_instance_exists = True
            instance_status = instance['status']
            break
    if not is_instance_exists:
        try:
            request = _create_instance(compute, project_id, image_project, image_family, zone, instance_name, machine_type)
            response = request.execute()
            print("Launching the VM instance")
            _wait_for_operation(compute, project_id, zone, response['name'])
            time.sleep(75)
            is_deployed = deploying_gcp_instance(deploy_dir, instance_name, zone)
            if not is_deployed:
                print ("Deleting the instance as deployment was not Successfull")
                request = _delete_instance(compute=compute, project=project_id, zone=zone, instance=instance_name)
                response = request.execute()
                _wait_for_operation(compute, project_id, zone, response['name'])
                print ("Try re-running the command")
        except HttpError as err:
            print (json.loads(err.content).get('error').get('errors')[0])
            return
        except:
            print (traceback.format_exc())
            return
    else:
        if instance_status != 'RUNNING':
            print ("Instance is not running. Restarting the instance")
            try:
                request = _start_instance(compute, project_id, zone, instance_name)
                response = request.execute()
                _wait_for_operation(compute, project_id, zone, response['name'])
            except HttpError as err:
                print (json.loads(err.content).get('error').get('errors')[0])
                return
            except:
                print (traceback.format_exc())
                return
        else:
            print ("Instance is already up and running. Moving forward to Deployment")
        is_deployed = deploying_gcp_instance(deploy_dir, instance_name, zone)
        if not is_deployed:
            print ("Deployment was not Successful. Try re-running the command")
    return is_deployed
 
def stop_gcp_instance(project_id, instance_name, zone):
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)
    try:
        request = _stop_instance(compute, project_id, zone, instance_name)
        response = request.execute()
        _wait_for_operation(compute, project_id, zone, response['name'])
        print ("Instance is successfully stopped")
    except HttpError as err:
        print (json.loads(err.content).get('error').get('errors')[0])
        return
    except:
        print (traceback.format_exc())
        return