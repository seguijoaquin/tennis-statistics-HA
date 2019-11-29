#!/usr/bin/env python3

import os
import logging
from constants import END, CLOSE, OK
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
OK_ENCODED = OK.encode()

class Terminator:
    def __init__(self, processes_number, in_exchange, group_exchange, next_exchange, next_exchange_type, next_routing_keys):
        self.processes_number = processes_number
        self.next_routing_keys = next_routing_keys
        self.closed = {}

        self.in_queue = RabbitMQQueue(exchange=in_exchange, consumer=True, exclusive=True)
        self.group_queue = RabbitMQQueue(exchange=group_exchange)
        self.next_queue = RabbitMQQueue(exchange=next_exchange, exchange_type=next_exchange_type)

    def run(self):
        self.in_queue.consume(self.close)

    def close(self, ch, method, properties, body):
        data = body.decode().split()
        if data[1] == END:
            for i in range(self.processes_number):
                body = ','.join([data[0], CLOSE])
                self.group_queue.publish(body)
                logging.info('Sent %s' % body)
            return

        if data[1] == OK:
            id = data[0]
            self.closed[id] = self.closed.get(id, 0) + 1

            if self.closed[id] == self.processes_number:
                for routing_key in self.next_routing_keys.split('-'):
                    body = ','.join([id, END])
                    self.next_queue.publish(body, routing_key)
                    logging.info('Sent %s' % body)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    processes_number = int(os.environ['PROCESSES_NUMBER'])
    in_exchange = os.environ['IN_EXCHANGE']
    group_exchange = os.environ['GROUP_EXCHANGE']
    next_exchange = os.environ['NEXT_EXCHANGE']
    next_exchange_type = os.environ['NEXT_EXCHANGE_TYPE']
    next_routing_keys = os.environ['NEXT_ROUTING_KEYS']

    terminator = Terminator(processes_number, in_exchange,
                            group_exchange, next_exchange,
                            next_exchange_type, next_routing_keys)
    terminator.run()
