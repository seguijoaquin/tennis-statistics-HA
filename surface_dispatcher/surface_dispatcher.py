#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, FILTERED_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

SURFACES = ['Hard', 'Clay', 'Carpet', 'Grass']
SURFACE_EXCHANGE = 'surfaces'
FILTERED_QUEUE = 'matches_surface'
TERMINATOR_EXCHANGE = 'dispatcher_terminator'

class SurfaceDispatcher:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=FILTERED_EXCHANGE, exchange_type='direct',
                                      consumer=True, queue_name=FILTERED_QUEUE,
                                      routing_keys=['dispatcher'])
        self.out_queue = RabbitMQQueue(exchange=SURFACE_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self, _):
        self.in_queue.consume(self.dispatch)

    def dispatch(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')

        if data[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if data[1] == CLOSE:
            body = ','.join([data[0], OK])
            self.terminator_queue.publish(body)
            logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        id = data[0]
        surface = data[4]
        minutes = data[10]

        if minutes == '' or surface in ('', 'None'):
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        body = ','.join([id, minutes])
        self.out_queue.publish(body, surface)
        logging.info('Sent %s to %s accumulator' % (body, surface))
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    hb = heartbeatprocess.HeartbeatProcess.setup(SurfaceDispatcher)
    hb.run()
