#!/usr/bin/env python3

import os
import logging
from constants import END
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()

class Accumulator:
    def __init__(self, routing_key, exchange, output_exchange):
        self.routing_key = routing_key
        self.total = 0
        self.amount = 0.0
        self.in_queue = RabbitMQQueue(exchange=exchange, exchange_type='direct',
                                      consumer=True, exclusive=True,
                                      routing_keys=routing_key.split('-'))
        self.out_queue = RabbitMQQueue(exchange=output_exchange)

    def run(self):
        self.in_queue.consume(self.add)

    def add(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        if body == END_ENCODED:
            body = ','.join([self.routing_key, str(self.amount), str(self.total)])
            self.out_queue.publish(body)
            self.in_queue.cancel()
            return

        self.total += float(body.decode())
        self.amount += 1
        logging.debug('Current total: %f' % self.total)
        logging.debug('Current amount: %f' % self.amount)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    routing_key = os.environ['ROUTING_KEY']
    exchange = os.environ['EXCHANGE']
    output_exchange = os.environ['OUTPUT_EXCHANGE']
    accumulator = Accumulator(routing_key, exchange, output_exchange)
    accumulator.run()
