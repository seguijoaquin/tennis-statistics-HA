FROM python:3.7-alpine

RUN pip install pika

COPY ./age_calculator/ /age_calculator/
COPY ./constants/constants.py /age_calculator/
COPY ./middleware/rabbitmq_queue.py /age_calculator/

WORKDIR /age_calculator/
