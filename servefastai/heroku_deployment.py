import os
import json
import shutil
from pathlib import Path
import sqlite3
import traceback
import time
from servefastai import common_helper

CONFIG_DIR = Path.home()/'.servefastai'
CONFIG_FNAME = 'config.json'
HEROKU_IMAGE_SUCCESS = ["Your image has been successfully pushed. You can now release it with the 'container:release' command."]

def deploy_heroku(app_name, deploy_dir):
    """
    """
    
    if not os.path.exists(CONFIG_DIR):
        print ("Create " + str(CONFIG_DIR + "as mentioned in README"))
        return
    
    with open(CONFIG_DIR/CONFIG_FNAME) as f:
        config_file_dict = json.load(f)
    
    username = config_file_dict["heroku"]["username"]
    print ("Logging into Heroku")
    heroku_login_result = common_helper.run_subprocess('heroku container:login')
    if heroku_login_result[0].lower() != 'login succeeded':
        print (heroku_login_result[1])
        return
    print ("Logging into Docker")
    docker_login_result = common_helper.run_subprocess('docker login --username=' + username +' --password=$(heroku auth:token)     registry.heroku.com')

    #TODO: check docker login result 
    available_apps_result = common_helper.run_subprocess('heroku apps')
    
    if app_name not in available_apps_result[0].split(' ')[2].splitlines():
        print ("Creating the app")
        create_app = common_helper.run_subprocess('heroku create ' + app_name)
        if not create_app[0]:
            print ("Error: " + create_app[1])
            return False
    else:
        print (app_name + " App is present. Moving Forward to Deployment")
    print ("Pushing the image to heroku repository")
    heroku_container_push = common_helper.run_subprocess('cd '+ deploy_dir +' && heroku container:push web -a ' + app_name)
    if heroku_container_push[0].split('\n')[-1].splitlines() != HEROKU_IMAGE_SUCCESS:
        print ("Error: " + heroku_container_push[1])
        return False
    #TODO: Parse Container build results.
    print ("Releasing the image")
    heroku_container_release = common_helper.run_subprocess('cd '+ deploy_dir +' && heroku container:release web -a ' + app_name)
    message = ['Releasing images web to %s... done'%(app_name)]
    if heroku_container_release[1].split('\n')[-1].splitlines() != message:
        print ("Error: " + heroku_container_release[1])
        return False
    return True
    
    
    
    