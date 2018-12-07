#!/bin/bash

if [ -z "$(docker ps -a -q)" ]
then
      echo "Starting the Container"     
else
     echo "Stopping the currently running container and staring the new one."
     docker stop $(docker ps -a -q) > /dev/null
     docker rm $(docker ps -a -q) > /dev/null
fi
docker run -p 5000:5000 -d --name python-server servefastai-image