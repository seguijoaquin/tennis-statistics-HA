FROM python:3.7-alpine

RUN pip install pika

COPY ./surface_dispatcher/ /surface_dispatcher/
COPY ./constants/constants.py /surface_dispatcher/
COPY ./middleware/rabbitmq_queue.py /surface_dispatcher/

WORKDIR /surface_dispatcher/
