#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, DISPATCHER_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

SURFACES = ['Hard', 'Clay', 'Carpet', 'Grass']
END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
SURFACE_EXCHANGE = 'surfaces'
DISPATCHER_QUEUE = 'matches_surface'
TERMINATOR_EXCHANGE = 'dispatcher_terminator'

class SurfaceDispatcher:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=DISPATCHER_EXCHANGE, consumer=True, queue_name=DISPATCHER_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=SURFACE_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.dispatch)

    def dispatch(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')

        if data[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            return

        if data[1] == CLOSE:
            body = ','.join([data[0], OK])
            self.terminator_queue.publish(body)
            logging.info('Sent %s' % body)
            return

        id = data[0]
        surface = data[4]
        minutes = data[10]

        if minutes == '' or surface in ('', 'None'):
            return

        body = ','.join([id, minutes])
        self.out_queue.publish(body, surface)
        logging.info('Sent %s to %s accumulator' % (body, surface))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    dispatcher = SurfaceDispatcher()
    dispatcher.run()
