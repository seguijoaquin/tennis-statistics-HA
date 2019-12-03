FROM python:3.7-alpine

RUN pip install pika

COPY ./leader/ /leader/
COPY ./constants/constants.py /leader/
COPY ./middleware/rabbitmq_queue.py /leader/

WORKDIR /leader/
