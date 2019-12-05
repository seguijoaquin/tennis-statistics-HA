#!/usr/bin/env python3

import logging
import os
from constants import END, DATABASE_EXCHANGE, RESPONSE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

FILES = ['surface', 'hand', 'age']

class Database:
    def __init__(self):
        self.count = {}
        self.in_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct',
                                      consumer=True, exclusive=True, routing_keys=FILES)

    def run(self, _):
        self.in_queue.consume(self.persist)

    def persist(self, ch, method, properties, body):
        logging.info('Received %r from %s' % (body, method.routing_key))
        data = body.decode().split(',')
        id = data[0]
        result = data[1]

        if result == END:
            self.count[id] = self.count.get(id, 0) + 1

            if self.count[id] != 3:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            for filename in FILES:
                try:
                    file = open(filename + id, 'r')
                    response = file.read()
                    file.close()
                except FileNotFoundError:
                    response = '%s: No results' % filename

                out_queue = RabbitMQQueue(exchange=RESPONSE_EXCHANGE + ':' + id)
                out_queue.publish(response)
                logging.info('Sent %s' % response)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        file = open(method.routing_key + id, 'a+')
        file.write(result + '\n')
        file.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    hb = heartbeatprocess.HeartbeatProcess.setup(Database)
    hb.run()
