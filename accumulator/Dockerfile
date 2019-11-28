FROM python:3.7-alpine

RUN pip install pika

COPY ./accumulator/ /accumulator/
COPY ./constants/constants.py /accumulator/
COPY ./middleware/rabbitmq_queue.py /accumulator/

WORKDIR /accumulator/
