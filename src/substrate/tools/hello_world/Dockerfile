FROM ubuntu:focal

RUN apt update && \
	apt install -y \
		python3-pip \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install Flask flask-cors

WORKDIR /data
