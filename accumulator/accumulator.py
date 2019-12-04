#!/usr/bin/env python3

import os
import logging
from constants import END
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

class Accumulator:
    def __init__(self, routing_key, exchange, output_exchange):
        self.routing_key = routing_key
        self.values = {}
        self.in_queue = RabbitMQQueue(exchange=exchange, exchange_type='direct',
                                      consumer=True, exclusive=True,
                                      routing_keys=routing_key.split('-'))
        self.out_queue = RabbitMQQueue(exchange=output_exchange)

    def run(self, _):
        self.in_queue.consume(self.add)

    def add(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        id = data[0]

        if data[1] == END:
            [amount, total] = self.values[id]
            body = ','.join([id, self.routing_key, str(amount), str(total)])
            self.out_queue.publish(body)
            logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if not id in self.values:
            self.values[id] = [0, 0]

        self.values[id][0] += 1
        logging.debug('Current amount: %f' % self.values[id][0])
        self.values[id][1] += float(data[1])
        logging.debug('Current total: %f' % self.values[id][1])
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    routing_key = os.environ['ROUTING_KEY']
    exchange = os.environ['EXCHANGE']
    output_exchange = os.environ['OUTPUT_EXCHANGE']

    hb = heartbeatprocess.HeartbeatProcess.setup(Accumulator, routing_key, exchange, output_exchange)
    hb.run()

