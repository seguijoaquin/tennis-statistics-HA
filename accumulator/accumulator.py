#!/usr/bin/env python3

import os
import logging
from constants import END
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

class Accumulator:
    def __init__(self, routing_key, exchange, output_exchange):
        self.hostname = os.environ['HOSTNAME']
        self.routing_key = routing_key
        self.values = {}
        self.in_queue = RabbitMQQueue(exchange=exchange, exchange_type='direct',
                                      consumer=True, queue_name='{}_queue'.format(self.hostname),
                                      routing_keys=routing_key.split('-'))
        self.out_queue = RabbitMQQueue(exchange=output_exchange)
        self.storage_queue = RabbitMQQueue(exchange='storage_input')
        self.data_queue = RabbitMQQueue(exchange='storage_output', exchange_type='direct',
                                        consumer=True, exclusive=True,
                                        routing_keys=[self.hostname])

    def run(self, _):
        cmd = ';'.join(['CATCHUP', self.hostname])
        self.storage_queue.publish(cmd)
        logging.info('Sent %s to storage' % cmd)
        self.data_queue.consume(self.update_values)
        self.in_queue.consume(self.add)

    def update_values(self, ch, method, properties, body):
        data = body.decode()
        if data == 'END':
            logging.info('State of %s updated' % self.hostname)
            self.data_queue.cancel()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        params = data.split(';')
        id = params[-1]
        values = params[2].split(',')
        amount = int(values[0])
        total = float(values[1])
        self.values[id] = [amount, total]
        logging.info('Values of %s updated: [%d, %f]' % (id, amount, total))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def add(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        id = data[0]

        if data[1] == END:
            [amount, total] = self.values[id]
            body = ','.join([id, self.routing_key, str(amount), str(total)])
            self.out_queue.publish(body)
            logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if not id in self.values:
            self.values[id] = [0, 0]

        self.values[id][0] += 1
        amount = self.values[id][0]
        logging.debug('Current amount: %f' % amount)

        self.values[id][1] += float(data[1])
        total = self.values[id][1]
        logging.debug('Current total: %f' % total)

        values = ','.join([str(amount), str(total)])
        cmd = ';'.join(['WRITE', self.hostname, values, id])
        self.storage_queue.publish(cmd)

        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    routing_key = os.environ['ROUTING_KEY']
    exchange = os.environ['EXCHANGE']
    output_exchange = os.environ['OUTPUT_EXCHANGE']

    hb = heartbeatprocess.HeartbeatProcess.setup(Accumulator, routing_key, exchange, output_exchange)
    hb.run()
