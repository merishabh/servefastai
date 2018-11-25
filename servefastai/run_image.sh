#!/bin/bash

docker stop $(docker ps -a -q) > /dev/null
docker run -p 5000:5000 -d servefastai-image