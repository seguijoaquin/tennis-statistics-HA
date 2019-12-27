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
        self.input_queue = RabbitMQQueue(exchange='storage_slave', consumer=True, queue_name='slave{}_queue'.format(pid))
        self.output_queue = RabbitMQQueue(exchange='storage_output', exchange_type='direct')
        self.master_queue = RabbitMQQueue(exchange='storage_input', consumer=True, queue_name='master_queue')
        self.instance_queue = RabbitMQQueue(exchange='storage_internal_{}'.format(pid), consumer=True, queue_name='storage_internal_{}'.format(pid))
        self.heartbeatproc = None

    def run(self, heartbeatproc):
        self.heartbeatproc = heartbeatproc
        self.heartbeatproc.metadata = self.role
        self.input_queue.consume(self.process)
        self.instance_queue.consume(self.listen)

    def process(self, ch, method, properties, body):
        if self.role == SLAVE_ROLE:
            logging.info('[SLAVE] Received %r' % body)
            msg = body.decode()
            parts = msg.split(",")
            if parts[0] == MASTER_NEEDED_MSG:
                # New master message
                if int(parts[1]) == int(self.pid):
                    # and I am the new master
                    logging.info('[SLAVE] I was asked to be the new Storage Master')
                    self.role = MASTER_ROLE
                    # start sending new role in heartbeats
                    self.heartbeatproc.metadata = self.role
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self.instance_queue.publish(MASTER_NEEDED_MSG)
                    self.input_queue.cancel()
                else:
                    logging.info('[SLAVE] I received a master message but I was not the target')
                    # I am not the new master, discard it
                    ch.basic_ack(delivery_tag=method.delivery_tag)
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
            self.input_queue.publish(body)
        if ch.is_open:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def persistState(self, body):
        state = body.decode()
        logging.info('Persisting to disk {%r}' % state)
        # MSG = CMD;tipoNodo_nroNodo;estado;job_id
        # EJ: WRITE;joiner_3;93243;123123
        params = state.split(';')
        # path = "/storage/nodeType_nodeNumber/"
        path = BASE_PATH + params[1] + "/"
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        # filename = "job_id"
        filename = params[-1] + ".state"
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
        # MSG = CMD;tipoNodo_nroNodo
        # EJ: READ;joiner_3
        params = msg.decode().split(';')
        path = BASE_PATH + params[1] + "/"
        client_routing_key = params[1]

        for filename in glob(path + "*.state"):
            with open(filename, 'r') as file:
                contents = file.read()
                self.output_queue.publish(contents, client_routing_key)

        self.output_queue.publish('END', client_routing_key)

if __name__ == '__main__':
    from watchdog import heartbeatprocess
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)

    pid = os.environ['PID']
    #storage = Storage(pid)
    #storage.run()

    #proc = ElectableProcess(pid, pidlist, wp.run)
    hb = heartbeatprocess.HeartbeatProcess.setup(Storage, pid)
    hb.run()
