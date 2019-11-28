FROM python:3.7-alpine

RUN pip install pika

COPY ./client/ /client/
COPY ./constants/constants.py /client/
COPY ./middleware/rabbitmq_queue.py /client/

WORKDIR /client/
