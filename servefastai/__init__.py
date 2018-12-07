import json
import os
import shutil
import subprocess
import json
import sys
import dill
import torch
import time
import sqlite3
import traceback
import logging
from pathlib import Path
from typing import List
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from servefastai import common_helper, gcp_deployment, heroku_deployment



CONFIG_DIR = Path.home()/'.servefastai'
CONFIG_FNAME = 'config.json'
DB_NAME = 'servefast.db'
HOST_ADD_WARNING = 'Failed to add the host to the list of known hosts (' + os.path.join(Path.home(), '.ssh/google_compute_known_hosts') + ').'
class ServeFastAI():

    DEPLOY_MODES = ["heroku", "gcp", "local"]

    def __init__(self, deploy_mode, deploy_dir="deploy",model_weights_path=None, output_classes=[], image_size=299, model_arch=None):
        """
        
        """
        if deploy_mode in self.DEPLOY_MODES:
            self.deploy_mode = self.DEPLOY_MODES.index(deploy_mode)
        else:
            print("Please choose heroku, gcp or local for deployment")
            return
        self.deploy_dir = deploy_dir
        self.model_weights_path = model_weights_path
        self.output_classes = output_classes
        self.image_size = image_size
        self.model_arch = model_arch
        try:
            common_helper._code_deploy(self.deploy_mode, self.deploy_dir, self.model_weights_path, self.output_classes, self.image_size, self.model_arch)
        except Exception as e:
            print (e)
            return
            
    def create_and_deploy(self):
        """
        
        """
        
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        if self.deploy_mode == 1:
            print ("Creating GCP instance")
            cursor.execute("CREATE TABLE IF NOT EXISTS gcp_instances_info (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id text, instance_name text, zone text, num_of_cpus INTEGER, amount_of_memory_per_cpu INTEGER);")
            self.project_id = "first-project-222114"#input("Id of the project?)
            self.instance_name = input("Name of the instance?")
            print ("This instance will use ubuntu-16 as OS version.")
            self.zone = input("Zone for this instance?")
            self.num_of_cpus = input("Number of cpus for this instance?")
            self.amount_of_memory_per_cpu = input("Amount of memory per cpu(MB)? (Give atleast 3 GB of size as FastAI might not install if it is lesser than that)")
            
            cursor.execute('''insert into gcp_instances_info (project_id, instance_name, zone, num_of_cpus,  amount_of_memory_per_cpu) values (?, ?, ?, ?, ?)''', (self.project_id, self.instance_name, self.zone, self.num_of_cpus, self.amount_of_memory_per_cpu))
        elif self.deploy_mode == 0:
            print ("Creating Heroku App")
            cursor.execute("CREATE TABLE IF NOT EXISTS heroku_apps_info (id INTEGER PRIMARY KEY AUTOINCREMENT, app_name text);")
            self.app_name = input("Name of the app?")
            cursor.execute('''insert into heroku_apps_info (app_name) values (?)''', (self.app_name,))
        try:
            is_deployed = self.deploy()
            if is_deployed:
                conn.commit()
                print ("Deployment has completed SuccessFully!!!")
        except Exception as e:
                print (e)
        finally:
            if conn:
                conn.close()
                
    def stop_given_gcp_instance(self):
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        self.list_gcp_instances()
        while True:
            deploy_id = int(input("Choose the instance id from the above list"))
            cursor.execute("select project_id, instance_name, zone, num_of_cpus, amount_of_memory_per_cpu from heroku_apps_info where id = ?", (deploy_id,))
            row = cursor.fetchone()
            if row:
                break
            print ("No instance found for the corresponding id. Please choose the correct id from the above list.")
        self.project_id, self.instance_name, self.zone, self.num_of_cpus, self.amount_of_memory_per_cpu = row
        gcp_deployment.stop_gcp_instance(self.project_id, self.instance_name, self.zone)
        if conn:
            conn.close()
            
    def list_gcp_and_heroku_instances(self):
        """
        
        """
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        self.list_gcp_instances()
        self.list_heroku_apps()
        conn.commit()
        conn.close()
        
    def list_gcp_instances(self):
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            print ("GCP Instances List\n")
            cursor.execute("select * from gcp_instances_info")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            return True
        except Exception as err:
            print ("No data found in GCP Instances Info Table.")
            return False
        finally:
            if conn:
                conn.close()
     
    def list_heroku_apps(self):
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            print ("Heroku Instances List\n")
            cursor.execute("select * from heroku_apps_info")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            return True
        except Exception as err:
            print ("No data found in Heroku Apps Info Table.")
            return False
        finally:
            if conn:
                conn.close()
            
    def reDeploy(self):
        conn = common_helper.get_sqlite_connection()
        cursor = conn.cursor()
        
        if self.deploy_mode == 1:
            if not self.list_gcp_instances():
                return
            while True:
                deploy_id = int(input("Choose the instance id from the above list"))
                cursor.execute("select project_id, instance_name, zone, num_of_cpus, amount_of_memory_per_cpu from gcp_instances_info where id = ?", (deploy_id,))
                row = cursor.fetchone()
                if row:
                    break
                print ("No instance found for the corresponding id. Please choose the correct id from the above list.")
            self.project_id, self.instance_name, self.zone, self.num_of_cpus, self.amount_of_memory_per_cpu = row
        elif self.deploy_mode == 0:
            if not self.list_heroku_apps():
                return
            while True:
                deploy_id = int(input("Choose the app id from the above list"))
                cursor.execute("select app_name from heroku_apps_info where id = ?", (deploy_id,))
                row = cursor.fetchone()
                if row:
                    break
                print ("No app found for the corresponding id. Please choose the correct id from the above list.")
            self.app_name = row[0]
        try:
            is_deployed = self.deploy()
            if is_deployed:
                print ("Deployment has completed SuccessFully!!!")
        except Exception as e:
                print (e)
        finally:
            if conn:
                conn.close()
                
            
    def deploy(self):
        if self.deploy_mode == 0:
            deployment_status = heroku_deployment.deploy_heroku(self.app_name, self.deploy_dir)
        elif self.deploy_mode == 1:
            deployment_status = gcp_deployment.deploy_gcp(deploy_dir = self.deploy_dir , project_id = self.project_id, instance_name = self.instance_name, zone = self.zone, num_of_cpus = self.num_of_cpus, amount_of_memory_per_cpu = self.amount_of_memory_per_cpu)
        return deployment_status

   