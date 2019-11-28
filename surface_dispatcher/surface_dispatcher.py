#!/usr/bin/env python3

import pika
import logging
from constants import END, CLOSE, OK, MATCHES_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

SURFACES = ['Hard', 'Clay', 'Carpet', 'Grass']
END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
SURFACE_EXCHANGE = 'surfaces'
MATCHES_QUEUE = 'matches_surface'
TERMINATOR_EXCHANGE = 'dispatcher_terminator'

class SurfaceDispatcher:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE, consumer=True, queue_name=MATCHES_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=SURFACE_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.dispatch)

    def dispatch(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        if body == END_ENCODED:
            self.terminator_queue.publish(END)
            return

        if body == CLOSE_ENCODED:
            self.terminator_queue.publish(OK)
            self.in_queue.cancel()
            return

        data = body.decode().split(',')
        surface = data[3]
        minutes = data[9]

        if minutes == '' or surface in ('', 'None'):
            return

        self.out_queue.publish(minutes, surface)
        logging.info('Sent %s minutes to %s accumulator' % (minutes, surface))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    dispatcher = SurfaceDispatcher()
    dispatcher.run()
