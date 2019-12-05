#!/usr/bin/env python3

import os
import logging
import pathlib
from glob import glob
from multiprocessing import Process
from rabbitmq_queue import RabbitMQQueue

MASTER_NEEDED_MSG = 'M'
SLAVE_ROLE  = 'slave'
MASTER_ROLE = 'master'
CATCHUP_COMMAND = 'CATCHUP'
WRITE_COMMAND = 'WRITE'
BASE_PATH = "/data/"

class Storage:
    def __init__(self, pid):
        self.pid = pid
        self.role = SLAVE_ROLE
        self.slaves = RabbitMQQueue(exchange='storage_slave')
        self.input_queue = RabbitMQQueue(exchange='storage_slave', consumer=True, exclusive=False, queue_name='slave{}_queue'.format(pid))
        self.output_queue = RabbitMQQueue(exchange = 'storage_output') 
        self.master_queue = RabbitMQQueue(exchange = 'storage_input', consumer = True, queue_name = 'master_queue')                           
        self.instance_subscriber = RabbitMQQueue(exchange='storage_internal_{}'.format(pid), consumer=True, exclusive=False, queue_name='storage_internal_{}'.format(pid))
        self.instance_publisher = RabbitMQQueue(exchange='storage_internal_{}'.format(pid))
        
    def run(self):
        self.input_queue.consume(self.process)
        self.instance_subscriber.consume(self.listen)

    def process(self, ch, method, properties, body):
        if self.role == SLAVE_ROLE:
            logging.info('[SLAVE] Received %r' % body)
            msg = body.decode()
            if msg == MASTER_NEEDED_MSG:
                logging.info('[SLAVE] I was asked to be the new Storage Master')
                self.role = MASTER_ROLE
                if ch.is_open:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                self.instance_publisher.publish(MASTER_NEEDED_MSG)
                self.input_queue.cancel()
                return
            logging.info('[SLAVE] Saving message')
            self.persistState(body)
        if ch.is_open:
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def listen(self, ch, method, properties, body):
        logging.info('[MASTER] I am consuming from storage_input')
        self.master_queue.consume(self.processMaster)

    def processMaster(self, ch, method, properties, body):
        logging.info('[MASTER] Received %r' % body)
        if self.isReadRequest(body):
            self.processRead(body)
        if self.isWriteRequest(body):
            self.persistState(body)
            self.slaves.publish(body)
        if ch.is_open:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def persistState(self, body):
        state = body.decode()
        logging.info('Persisting to disk {%r}' % state)
        # MSG = CMD;tipoNodo_nroNodo;estado;ids_vistos;timestamp;job_id
        # EJ: WRITE;joiner_3;93243;10,11,12,13;20191206113249;123123
        params = state.split(';')
        storageShard = self.getStorageShard(params[5]) # Shard storage data by job_id into 2 clusters
        # path = "/storage/shard_id/nodeType_nodeNumber/"
        path = BASE_PATH + str(storageShard) + "/" + str(params[1]) + "/"
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        # filename = "job_id"
        filename = str(params[5]) + ".state"
        f = open(path + filename, "w+") # Truncates previous state & writes
        f.write(str(state))
        f.close()
        logging.info('Persisted {%r}' % state)

    def isReadRequest(self, b):
        if CATCHUP_COMMAND in b.decode():
            return True
        return False

    def isWriteRequest(self, b):
        if WRITE_COMMAND in b.decode():
            return True
        return False

    def processRead(self, msg):
        # MSG = CMD;tipoNodo_nroNodo;timestamp
        # EJ: READ;joiner_3;20191201312312
        params = msg.decode().split(';')
        storageShard = self.getStorageShard(params[3])
        filename = params[1]
        filePath = BASE_PATH + str(storageShard) + "/" +str(filename) + "/"

        for file in glob(filePath + "*.state"):
            with open(filename, 'r') as file:
                contents = file.read()
                client_routing_key = str(filename)
                self.output_queue.publish(contents, client_routing_key)

        self.output_queue.publish('END', client_routing_key)

    def getStorageShard(self, id):
        return int(id) % 2

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    pid = os.environ['PID']
    storage = Storage(pid)
    storage.run()
