FROM ubuntu:jammy
SHELL ["/bin/bash", "--login", "-c"]

RUN apt update && apt -y upgrade && apt autoremove && apt install -y \
	curl \
	python3 \
	python3-pip

RUN curl -sSL https://get.docker.com/ | sh

RUN pip install seelabutk-substrate

WORKDIR /root
RUN curl -LO https://github.com/nvm-sh/nvm/archive/refs/tags/v0.39.1.tar.gz
RUN tar -xvzf v0.39.1.tar.gz
RUN nvm-0.39.1/install.sh
SHELL ["/bin/bash", "--login", "-i", "-c"]
RUN nvm install --lts
RUN npm install aws-cli

ENV PATH "${PATH}:/root/.nvm/versions/node/v16.17.1/bin"
