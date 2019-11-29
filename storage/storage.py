#!/usr/bin/env python3

import os
import logging
from multiprocessing import Process
from storage_master import StorageMaster
from storage_replica import StorageReplica
from rabbitmq_queue import RabbitMQQueue

class Storage:
    def __init__(self, pid):
        self.role = StorageReplica(pid)

    def run(self):
        self.role.run()

    def change_role(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        role = body.decode()
        if role == 'master':
            logging.info('Changing to master role')
            self.role = StorageMaster()
        else:
            logging.error('Role %s does not exist' % role)
            return

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    pid = os.environ['PID']
    storage = Storage(pid)
    storage.run()
