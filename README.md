# servefastai

Serve FastAI models and get a web-based UI to test them out with a single line of code. See a [video demo here](https://youtu.be/xwN7arEgvBg).

![screenshot](https://i.imgur.com/TzZQZUs.jpg)

---

# Table of contents

1. [Prerequisite](#pre)
2. [Deploying on GCP(Google Cloud Platform)](#gcp)
3. [Deploying on Heroku](#heroku)


---

<a name="pre"></a> 
# Prerequisite:

* Create the hidden folder in your home directory with the name same as .servefastai
* Create the config.json file inside the above folder. Format should be as below:
```
{
    "heroku": {
     "username": "<heroku-username>",
     "password": "<heroku-password>"
    }
}
```

---


<a name="gcp"></a> 

# Deploying on GCP(Google Cloud Platform):

* Create the account on [google cloud platform](https://cloud.google.com/).
* Login into google cloud [console](https://console.cloud.google.com).
* Create a new [project](https://console.cloud.google.com/projectcreate). Give the project name and project ID, remember the project id as it will be needed further for creating instances.
* Install the Google cloud sdk on your machine. Follow this [link](https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu#before-you-begin).
* Login on the terminal using this command - `gcloud auth login`
* Save the credentials in a file using this command - `gcloud auth application-default login`


---

**Creating a ServeFastAI Object**

Open the Jupyter Notebook in which you have the model pth file.
Execute the below commands on the notebook:

```
%load_ext autoreload
%autoreload 2
```
```
import sys
sys.path.append('/path/to/servefastai')
```
```
from servefastai import ServeFastAI
```
```
servefastai_object = ServeFastAI(deploy_mode="gcp", deploy_dir="deploy", model_weights_path="/path/to/pth/file", output_classes=output_classes, image_size=64, model_arch="resnet18" )
```

Above Code will create the ServeFastAI object(``servefastai_object``) which has below attributes:

deploy_mode - "gcp"  
deploy_dir - Local "deploy" directory will be created with this name. This folder will be used for deploying your model on the instance.  
model_weights_path - full path of your model pth  
output_classes - output classes  
image_size - image size  
model_arch - Specify the correct resnet model, resnet18 or resnet36  

---

**Creating and Deploying a new GCP instance:**

```
servefastai_object.create_and_deploy()
```
This might be helpful while creating the instance:
[Zone list](https://cloud.google.com/compute/docs/regions-zones/#available)

Above function will create the instance in your created project id and deploy your model to it.
Once that is done, you need to add the Firewall rules and the External IP to that instance.

*Adding the FireWall rule and External IP*:

1.Follow this [link](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address#IP_assign), for creating the external IP and attaching it to the existing VM instance.

2.Add the Firewall rule. Which should look like this.
![alt text](https://www.dropbox.com/s/bcr04lwgd7gxiti/firewall_rule.png?raw=true)

Access the server using the External IP and Port 5000.You will see a form where you can upload one or more images. Upload the images and click submit to view the predictions.

---

**Redeploying the code with the existing GCP instances**

* Initialize the below servefastai object with the new attributes.

```
servefastai_object = ServeFastAI(deploy_mode="gcp", deploy_dir="deploy", model_weights_path="/path/to/pth/file", output_classes=output_classes, image_size=64, model_arch="resnet18" )
```

* Run the following function and enter the details as asked in the function.

```
servefastai_object.reDeploy()
```

---

**Listing the GCP instances**

```
servefastai_object.list_gcp_instances()
```

**Stop the GCP instance**

```
servefastai_object.stop_given_gcp_instance()
```

<a name=“heroku”></a>
# Deploying on Heroku:

**Install Docker CE**

A. Your application deployed on Heroku would be running inside a Docker container, so you need to install Docker CE (community edition) locally on your computer.
Follow the instructions given [here](https://docs.docker.com/install/) to install Docker for your version of OS.

B. After installing Docker, add your current user to the docker group using below command. This will ensure that you don't have to type sudo for running any docker or heroku commands. You would have to logout and login again for the new permissions to take effect.
```
sudo usermod -aG docker $USER
```

C. Now check that docker installation is correctly done by running `docker ps` command. If you see any permission issue, then it most likely means you did not re-login.

---

**Prerequisites for Heroku**

A. Create your account on [Heroku](https://www.heroku.com/)  
B. Install Heroku CLI by following the instructions [here](https://devcenter.heroku.com/articles/heroku-cli#download-and-install).  
In brief, 
* Install snap or snapd (depending on platform). For my debian linux, I installed using following commands:  
   `sudo apt update`  
   `sudo apt install snapd` 
* `sudo snap install --classic heroku`  
I remember my heroku CLI getting installed in non-standard path somwehere in /snapd/, so create a symbolic link if you don't want the hassle of typing the path everytime.  
* Login to heroku using
`heroku auth:login -i`

---

**Creating a ServeFastAI Object**

Open the Jupyter Notebook in which you have the model pth file.
Execute the below commands on the notebook:

```
%load_ext autoreload
%autoreload 2
```
```
import sys
sys.path.append('/path/to/servefastai')
```
```
from servefastai import ServeFastAI
```
```
servefastai_object = ServeFastAI(deploy_mode="heroku", deploy_dir="deploy", model_weights_path="/path/to/pth/file", output_classes=output_classes, image_size=64, model_arch="resnet18" )
```

Above Code will create the ServeFastAI object(``servefastai_object``) which has below attributes:

`deploy_mode` - "heroku"  
`deploy_dir` - Local "deploy" directory will be created with this name. This folder will be used for deploying your model on the app.  
`model_weights_path` - full path of your model pth  
`output_classes` - output classes  
`image_size` - image size  
`model_arch` - Specify the correct resnet model, resnet18 or resnet36.  

---

**Creating and Deploying a new Heroku app:**

```
servefastai_object.create_and_deploy()
```

Access the server using the https://<your-app-name>.herokuapp.com/ .You will see a form where you can upload one or more images. Upload the images and click submit to view the predictions.

---

**Redeploying the code with the existing Heroku instances**

* Initialize the below servefastai object with the new attributes.
```
servefastai_object = ServeFastAI(deploy_mode="heroku", deploy_dir="deploy", model_weights_path="/path/to/pth/file", output_classes=output_classes, image_size=64, model_arch="resnet18" )
```
* Run the following function and enter the details as asked in the function.
```
servefastai_object.reDeploy()
```

---


**Listing the Heroku apps**
```
servefastai_object.list_heroku_apps()
```

---














