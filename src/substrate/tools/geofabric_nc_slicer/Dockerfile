FROM ubuntu:focal
RUN apt-get update && apt-get install python3.8 -y \
    python3-pip \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./app/requirements.txt /app/requirements.txt

WORKDIR "/app/"
RUN python3 -m pip install -r requirements.txt

COPY ./app/static /app/static/
COPY ./app/templates /app/templates/
COPY ./app/app.py /app/
COPY ./app/grapher.py /app/
COPY ./app/utils.py /app/

ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
