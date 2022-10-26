FROM ubuntu:jammy
SHELL ["/bin/bash", "--login", "-c"]

RUN apt update && apt -y upgrade && apt autoremove && apt install -y \
	curl \
	python3 \
	python3-pip \
	unzip

RUN curl -sSL https://get.docker.com/ | sh

WORKDIR /root
RUN curl -LO https://github.com/nvm-sh/nvm/archive/refs/tags/v0.39.1.tar.gz
RUN tar -xvzf v0.39.1.tar.gz
RUN nvm-0.39.1/install.sh
SHELL ["/bin/bash", "--login", "-i", "-c"]
RUN nvm install --lts

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN aws/install
RUN npm install aws-cdk aws-cdk-lib

RUN pip install seelabutk-substrate==1.5.5

ENV PATH "${PATH}:/root/.nvm/versions/node/v16.17.1/bin"
