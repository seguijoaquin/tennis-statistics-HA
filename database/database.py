#!/usr/bin/env python3

import logging
import os
from constants import END, DATABASE_EXCHANGE, RESPONSE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

FILES = ['surface', 'hand', 'age']

class Database:
    def __init__(self):
        self.hostname = os.environ['HOSTNAME']
        self.count = {}
        self.in_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct',
                                      consumer=True, queue_name='{}_queue'.format(self.hostname),
                                      routing_keys=FILES)
        self.storage_queue = RabbitMQQueue(exchange='storage_input')
        self.data_queue = RabbitMQQueue(exchange='storage_output', exchange_type='direct',
                                        consumer=True, exclusive=True,
                                        routing_keys=[self.hostname])

    def run(self, _):
        cmd = ';'.join(['CATCHUP', self.hostname])
        self.storage_queue.publish(cmd)
        logging.info('Sent %s to storage' % cmd)
        self.data_queue.consume(self.update_count)
        self.in_queue.consume(self.persist)

    def update_count(self, ch, method, properties, body):
        data = body.decode()
        if data == 'END':
            logging.info('State of %s updated' % self.hostname)
            self.data_queue.cancel()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        params = data.split(';')
        id = params[-1]
        count = int(params[2])
        self.count[id] = count
        logging.info('Count of %s updated: %d' % (id, count))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def persist(self, ch, method, properties, body):
        logging.info('Received %r from %s' % (body, method.routing_key))
        data = body.decode().split(',')
        id = data[0]
        result = data[1]

        if result == END:
            self.count[id] = self.count.get(id, 0) + 1
            cmd = ';'.join(['WRITE', self.hostname, str(self.count[id]), id])
            self.storage_queue.publish(cmd)

            if self.count[id] != 3:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            for filename in FILES:
                try:
                    file = open(filename + id, 'r')
                    response = file.read()
                    file.close()
                except FileNotFoundError:
                    response = '%s: No results' % filename

                out_queue = RabbitMQQueue(exchange=RESPONSE_EXCHANGE + ':' + id)
                out_queue.publish(response)
                logging.info('Sent %s' % response)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        file = open(method.routing_key + id, 'a+')
        file.write(result + '\n')
        file.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.INFO)

    hb = heartbeatprocess.HeartbeatProcess.setup(Database)
    hb.run()
