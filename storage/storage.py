#!/usr/bin/env python3

import os
import logging
from multiprocessing import Process
# from storage_master import StorageMaster
# from storage_slave import StorageSlave
from rabbitmq_queue import RabbitMQQueue

MASTER_NEEDED_MSG = 'M'
SLAVE_ROLE  = 'slave'
MASTER_ROLE = 'master'
READ_COMMAND = 'CATCHUP'

class Storage:
    def __init__(self, pid):
        self.pid = pid
        self.role = SLAVE_ROLE
        self.input_queue = RabbitMQQueue(exchange='slave', consumer=True, exclusive=True, queue_name='slave{}_queue'.format(pid))
        self.slaves = RabbitMQQueue(exchange='slave')
        self.master_queue = RabbitMQQueue(exchange = 'storage_input', consumer = True, queue_name = 'master_queue')
        self.output_queue = RabbitMQQueue(exchange = 'storage_output')                            
        
    def run(self):
        self.input_queue.consume(self.process)

    def process(self, ch, method, properties, body):
        if self.role == SLAVE_ROLE:
            logging.info('[SLAVE] Received %r' % body)
            msg = body.decode()
            if msg == MASTER_NEEDED_MSG:
                logging.info('[SLAVE] I was asked to be the new Storage Master')
                self.role = MASTER_ROLE
                # TODO: ACK message
                self.master_queue.consume(self.processMaster)
            logging.info('[SLAVE] Saving message')
            self.persistState(body)
            # TODO: ACK message


    def processMaster(self, ch, method, properties, body):
        logging.info('[MASTER] Received %r' % body)
        if self.isReadRequest(body):
            self.processRead(body)
        else:
            self.persistState(body)
            self.slaves.publish(body)
            # TODO: ACK msg

    def persistState(self, body):
        # TODO: Save state to disk
        logging.info('Persisting to disk %r' % body)

    def isReadRequest(self, msg):
        return False
        # return READ_COMMAND in msg

    def processRead(self, msg):
        # TODO: parse msg
        # TODO: fetch state from disk
        # TODO: build response
        response = '<STATE>'
        self.output_queue.publish(response)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    pid = os.environ['PID']
    storage = Storage(pid)
    storage.run()
