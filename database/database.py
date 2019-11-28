#!/usr/bin/env python3

import logging
from constants import END, DATABASE_EXCHANGE, RESPONSE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

FILES = ['surface', 'hand', 'age']

class Database:
    def __init__(self):
        self.count = 0
        self.in_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct',
                                      consumer=True, exclusive=True, routing_keys=FILES)
        self.out_queue = RabbitMQQueue(exchange=RESPONSE_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.persist)

    def persist(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        result = body.decode()
        if result == END:
            self.count += 1

            if self.count != 3:
                return

            for filename in FILES:
                file = open(filename, 'r')
                response = file.read()
                file.close()
                self.out_queue.publish(response)
                self.in_queue.cancel()
            return

        file = open(method.routing_key, 'a+')
        file.write(result + '\n')
        file.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)
    database = Database()
    database.run()
