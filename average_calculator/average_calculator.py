#!/usr/bin/env python3

import logging
from constants import END, DATABASE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

AVERAGE_CALCULATOR_EXCHANGE = 'surface_values'
ROUTING_KEY = 'surface'

class AverageCalculator:
    def __init__(self):
        self.count = {}
        self.in_queue = RabbitMQQueue(exchange=AVERAGE_CALCULATOR_EXCHANGE, consumer=True,
                                      exclusive=True)
        self.out_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct')

    def run(self, _):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        [id, surface, amount, total] = body.decode().split(',')
        avg = float(total) / float(amount)
        result = '{}: {} minutes'.format(surface, avg)
        body = ','.join([id, result])
        self.out_queue.publish(body, ROUTING_KEY)
        logging.info('Sent %s' % body)
        self.count[id] = self.count.get(id, 0) + 1
        if self.count[id] == 3:
            end = ','.join([id, END])
            self.out_queue.publish(end, ROUTING_KEY)
            logging.info('Sent %s' % end)
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    hb = heartbeatprocess.HeartbeatProcess.setup(AverageCalculator)
    hb.run()
