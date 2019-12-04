#!/usr/bin/env python3

import os
import logging
from constants import END, CLOSE, OK
from rabbitmq_queue import RabbitMQQueue

class Terminator:
    def __init__(self, processes_number, in_exchange, group_exchange, \
                 group_exchange_type, group_routing_key, next_exchange, \
                 next_exchange_type, next_routing_keys):
        self.processes_number = processes_number
        self.next_routing_keys = next_routing_keys
        self.group_routing_key = group_routing_key
        self.closed = {}

        self.in_queue = RabbitMQQueue(exchange=in_exchange, consumer=True, exclusive=True)
        self.group_queue = RabbitMQQueue(exchange=group_exchange, exchange_type=group_exchange_type)
        self.next_queue = RabbitMQQueue(exchange=next_exchange, exchange_type=next_exchange_type)

    def run(self):
        self.in_queue.consume(self.close)

    def close(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        if data[1] == END:
            for i in range(self.processes_number):
                body = ','.join([data[0], CLOSE])
                self.group_queue.publish(body, self.group_routing_key)
                logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if data[1] == OK:
            id = data[0]
            self.closed[id] = self.closed.get(id, 0) + 1

            if self.closed[id] == self.processes_number:
                for routing_key in self.next_routing_keys.split('-'):
                    body = ','.join([id, END])
                    self.next_queue.publish(body, routing_key)
                    logging.info('Sent %s' % body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    processes_number = int(os.environ['PROCESSES_NUMBER'])
    in_exchange = os.environ['IN_EXCHANGE']
    group_exchange = os.environ['GROUP_EXCHANGE']
    group_exchange_type = os.environ['GROUP_EXCHANGE_TYPE']
    group_routing_key = os.environ['GROUP_ROUTING_KEY']
    next_exchange = os.environ['NEXT_EXCHANGE']
    next_exchange_type = os.environ['NEXT_EXCHANGE_TYPE']
    next_routing_keys = os.environ['NEXT_ROUTING_KEYS']

    terminator = Terminator(processes_number, in_exchange, group_exchange,
                            group_exchange_type, group_routing_key,
                            next_exchange, next_exchange_type, next_routing_keys)
    terminator.run()
