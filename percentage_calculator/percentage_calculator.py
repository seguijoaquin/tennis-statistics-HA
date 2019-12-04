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
        self.hands = {}
        self.in_queue = RabbitMQQueue(exchange=HANDS_EXCHANGE, consumer=True, exclusive=True)
        self.out_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct')

    def run(self):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        [id, hand, amount, total] = body.decode().split(',')
        if not id in self.hands:
            self.hands[id] = [None, None]

        left = self.hands[id][1]
        if hand == RIGHT:
            self.hands[id][0] = float(amount)
            if self.hands[id][1] is None:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

        if hand == NO_RIGHT:
            self.hands[id][1] = float(amount)
            if self.hands[id][0] is None:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

        right_percentage = 100 * self.hands[id][0] / (self.hands[id][0] + self.hands[id][1])
        left_percentage = 100 - right_percentage
        right_response = 'R Victories: {}%'.format(right_percentage)
        left_response = 'L Victories: {}%'.format(left_percentage)

        body = ','.join([id, right_response])
        self.out_queue.publish(body, ROUTING_KEY)
        logging.info('Sent %s' % body)

        body = ','.join([id, left_response])
        self.out_queue.publish(body, ROUTING_KEY)
        logging.info('Sent %s' % body)

        body = ','.join([id, END])
        self.out_queue.publish(body, ROUTING_KEY)
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    calculator = PercentageCalculator()
    calculator.run()
