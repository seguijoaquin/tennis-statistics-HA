FROM python:3.7-alpine

RUN pip install pika

COPY ./different_hands_filter/ /different_hands_filter/
COPY ./constants/constants.py /different_hands_filter/
COPY ./middleware/rabbitmq_queue.py /different_hands_filter/

WORKDIR /different_hands_filter/
