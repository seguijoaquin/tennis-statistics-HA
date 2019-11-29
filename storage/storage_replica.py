#!/usr/bin/env python3

import logging
from rabbitmq_queue import RabbitMQQueue
from storage_master import StorageMaster

class StorageReplica:
    def __init__(self, pid):
        self.replica_queue = RabbitMQQueue(exchange='replica',
                                           consumer=True,
                                           exclusive=True,
                                           queue_name='replica{}_queue'.format(pid))

    def run(self):
        self.replica_queue.consume(self.persist)

    def persist(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        print(body) # Must be write
        # ch.basic_ack(delivery_tag=method.delivery_tag)
