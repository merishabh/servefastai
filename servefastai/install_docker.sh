#!/bin/bash

dpkg -s "docker-ce" &> /dev/null

if [ $? -eq 0 ]; then
    echo "Package is already installed!"
    exit
else
    echo "Package  is NOT installed! Installing"
fi

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
apt-cache policy docker-ce
sudo apt-get install -y docker-ce
sudo usermod -aG docker $USER