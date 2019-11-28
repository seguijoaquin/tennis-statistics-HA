#!/usr/bin/env python3

import pika
import logging
from constants import END, DATABASE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

ROUTING_KEY = 'hand'
RIGHT = 'R'
NO_RIGHT = 'L-U'
HANDS_EXCHANGE = 'hands_values'

class PercentageCalculator:
    def __init__(self):
        self.left = None
        self.right = None
        self.in_queue = RabbitMQQueue(exchange=HANDS_EXCHANGE, consumer=True, exclusive=True)
        self.out_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct')

    def run(self):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        [hand, amount, total] = body.decode().split(',')
        if hand == RIGHT:
            self.right = float(amount)
            if self.left is None:
                return

        if hand == NO_RIGHT:
            self.left = float(amount)
            if self.right is None:
                return

        right_percentage = 100 * self.right / (self.left + self.right)
        left_percentage = 100 - right_percentage
        right_response = 'R Victories: {}%'.format(right_percentage)
        left_response = 'L Victories: {}%'.format(left_percentage)
        self.out_queue.publish(right_response, ROUTING_KEY)
        self.out_queue.publish(left_response, ROUTING_KEY)
        self.out_queue.publish(END, ROUTING_KEY)
        self.in_queue.cancel()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    calculator = PercentageCalculator()
    calculator.run()
