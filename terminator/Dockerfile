FROM python:3.7-alpine

RUN pip install pika

COPY ./terminator/ /terminator/
COPY ./constants/constants.py /terminator/
COPY ./middleware/rabbitmq_queue.py /terminator/

WORKDIR /terminator/
