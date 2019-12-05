FROM python:3.7-alpine

RUN pip install pika

COPY ./storage/ /storage/
COPY ./middleware/rabbitmq_queue.py /storage/

WORKDIR /storage/
