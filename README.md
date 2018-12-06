# servefastai

Serve FastAI models and get a web-based UI to test them out with a single line of code. See a [video demo here](https://youtu.be/xwN7arEgvBg).

![screenshot](https://i.imgur.com/TzZQZUs.jpg)

Table of contents
1. [Deploying on GCP(Google Cloud Platform)](#gcp)
2. [Deploying on Heroku](#heroku)


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
model_arch - resnet18 or resnet36  

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















