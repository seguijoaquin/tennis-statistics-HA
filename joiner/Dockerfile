FROM python:3.7-alpine

RUN pip install pika

COPY ./joiner/ /joiner/
COPY ./constants/constants.py /joiner/
COPY ./middleware/rabbitmq_queue.py /joiner/

WORKDIR /joiner/
