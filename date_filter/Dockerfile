FROM python:3.7-alpine

RUN pip install pika

COPY ./date_filter/ /date_filter/
COPY ./constants/constants.py /date_filter/
COPY ./middleware/rabbitmq_queue.py /date_filter/

WORKDIR /date_filter/
