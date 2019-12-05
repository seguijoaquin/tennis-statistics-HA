#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, MATCHES_EXCHANGE, FILTERED_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

MATCHES_QUEUE = 'matches_queue'
TERMINATOR_EXCHANGE = 'date_filter_terminator'

class DateFilter:
    def __init__(self):
        self.acked = set()
        self.in_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE, consumer=True,
                                      queue_name=MATCHES_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=FILTERED_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self, _):
        self.in_queue.consume(self.filter)

    def filter(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        match = body.decode().split(',')
        if match[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if match[1] == CLOSE:
            id = match[0]
            if not id in self.acked:
                body = ','.join([id, OK])
                self.terminator_queue.publish(body)
                self.acked.add(id)
            else:
                self.in_queue.publish(body)
            logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        date_from = match[0]
        date_to = match[1]
        tourney_date = match[5]
        if tourney_date < date_from or tourney_date > date_to:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        data = ','.join(match[2:])
        self.out_queue.publish(data, 'joiner')
        self.out_queue.publish(data, 'dispatcher')
        logging.info('Sent %s' % data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    hb = heartbeatprocess.HeartbeatProcess.setup(DateFilter)
    hb.run()
