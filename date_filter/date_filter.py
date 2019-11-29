#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, MATCHES_EXCHANGE, FILTERED_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
MATCHES_QUEUE = 'matches_queue'

class DateFilter:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE, consumer=True,
                                      queue_name=MATCHES_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=FILTERED_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.filter)

    def filter(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        match = body.decode().split(',')
        if match[1] == END:
            self.out_queue.publish(body)
            return

        date_from = match[0]
        date_to = match[1]
        tourney_date = match[5]
        if tourney_date < date_from or tourney_date > date_to:
            return
        data = ','.join(match[2:])
        self.out_queue.publish(data)
        logging.info('Sent %s' % data)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    filter = DateFilter()
    filter.run()
