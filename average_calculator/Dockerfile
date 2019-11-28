FROM python:3.7-alpine

RUN pip install pika

COPY ./average_calculator/ /average_calculator/
COPY ./constants/constants.py /average_calculator/
COPY ./middleware/rabbitmq_queue.py /average_calculator

WORKDIR /average_calculator/
