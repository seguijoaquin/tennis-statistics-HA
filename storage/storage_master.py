#!/usr/bin/env python3

import logging
from rabbitmq_queue import RabbitMQQueue

class StorageMaster:
    def __init__(self):
        self.replica_queue = RabbitMQQueue(exchange='replica')
        self.master_queue = RabbitMQQueue(exchange='master', consumer=True, queue_name='master_queue')

    def run(self):
        self.master_queue.consume(self.persist)

    def persist(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        print(body) # Must be write
        self.replica_queue.publish(body)
