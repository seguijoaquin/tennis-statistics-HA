#!/usr/bin/env python3

import logging
from constants import END, DATABASE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

AVERAGE_CALCULATOR_EXCHANGE = 'surface_values'
ROUTING_KEY = 'surface'

class AverageCalculator:
    def __init__(self):
        self.count = 0
        self.in_queue = RabbitMQQueue(exchange=AVERAGE_CALCULATOR_EXCHANGE, consumer=True,
                                      exclusive=True)
        self.out_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct')

    def run(self):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        [surface, amount, total] = body.decode().split(',')
        avg = float(total) / float(amount)
        result = '{}: {} minutes'.format(surface, avg)
        self.out_queue.publish(result, ROUTING_KEY)
        self.count += 1
        if self.count == 3:
            self.out_queue.publish(END, ROUTING_KEY)
            self.in_queue.cancel()
        logging.info('Sent %s' % result)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    calculator = AverageCalculator()
    calculator.run()
