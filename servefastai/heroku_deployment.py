

def deploy_heroku(self):
        """
        """
        #README: Apt get install snapd, Heroku
        #LOgin to Heroku
        username = self.config_file_dict["heroku"]["username"]
        app_name = self.config_file_dict["heroku"]["app-name"]
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
            print (app_name + " App is already present")
        print ("Pushing the image to heroku repository")
        heroku_container_push = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:push web -a ' + app_name)
        #TODO: Parse Container build results.
        print ("Releasing the image")
        heroku_container_release = self.run_subprocess('cd '+ self.deploy_dir +' && heroku container:release web -a ' + app_name)