FROM python:3.7-alpine

RUN pip install pika

RUN apk update
RUN apk add docker && apk add docker-compose

RUN pip install pyyaml

COPY ./watchdog/ /watchdog/
COPY ./constants/constants.py /watchdog/
COPY ./middleware/rabbitmq_queue.py /watchdog/
COPY cluster_config.yml /watchdog/
COPY docker-compose.yml /watchdog/

WORKDIR /watchdog/
