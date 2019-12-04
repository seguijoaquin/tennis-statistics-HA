FROM python:3.7-alpine

RUN pip install pika

COPY ./percentage_calculator/ /percentage_calculator/
COPY ./constants/constants.py /percentage_calculator/
COPY ./middleware/rabbitmq_queue.py /percentage_calculator/
COPY ./watchdog/ /percentage_calculator/watchdog/

WORKDIR /percentage_calculator/
