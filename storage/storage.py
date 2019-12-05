#!/usr/bin/env python3

import os
import logging
import pathlib
from multiprocessing import Process
from rabbitmq_queue import RabbitMQQueue

MASTER_NEEDED_MSG = 'M'
SLAVE_ROLE  = 'slave'
MASTER_ROLE = 'master'
CATCHUP_COMMAND = 'CATCHUP'
BASE_PATH = "/storage/"

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
        else:
            self.persistState(body)
            self.slaves.publish(body)
            if ch.is_open:
                ch.basic_ack(delivery_tag=method.delivery_tag)

    def persistState(self, body):
        logging.info('Persisting to disk {%r}' % body)
        # MSG = CMD;tipoNodo_nroNodo;estado;ids_vistos;timestamp;job_id
        # EJ: WRITE;joiner_3;93243;10,11,12,13;20191206113249;123123
        params = body.decode().split(';')
        storageShard = self.getStorageShard(params[5]) # Shard storage data by job_id into 2 clusters
        # path = "/storage/shard_id/job_id/"
        path = BASE_PATH + str(storageShard) + "/" + str(params[5])
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        # filename = "nodeType_nodeNumber"
        filename = str(params[1])
        f = os.open(path + filename, "w+") # Truncates previous state & writes
        f.write(body)
        f.close()
        logging.info('Persisted {%r}' % body)

    def isReadRequest(self, b):
        if CATCHUP_COMMAND in b.decode():
            return True
        return False

    def processRead(self, msg):
        # MSG = CMD;tipoNodo_nroNodo;timestamp;job_id
        # EJ: READ;joiner_3;20191201312312;job_id
        params = msg.decode().split(';')
        storageShard = self.getStorageShard(params[3])
        job_id = params[3]
        filename = params[1]
        filePath = BASE_PATH + str(storageShard) + "/" +str(job_id) + "/" + str(filename)

        f = os.open(filePath, "r")
        contents = f.read()
        f.close()
        
        response = contents
        client_routing_key = str(job_id) + str(filename)
        self.output_queue.publish(response, client_routing_key)

    def getStorageShard(self, id):
        return id % 2

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    pid = os.environ['PID']
    storage = Storage(pid)
    storage.run()
