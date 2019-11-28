FROM python:3.7-alpine

RUN pip install pika

COPY ./database/ /database/
COPY ./constants/constants.py /database/
COPY ./middleware/rabbitmq_queue.py /database/

WORKDIR /database/
