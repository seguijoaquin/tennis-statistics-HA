#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, OUT_AGE_CALCULATOR_EXCHANGE, DATABASE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

AGE_DIFFERENCE_FILTER_QUEUE = 'age_queue'
ROUTING_KEY = 'age'
TERMINATOR_EXCHANGE = 'age_filter_terminator'

class AgeDifferenceFilter:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=OUT_AGE_CALCULATOR_EXCHANGE, consumer=True,
                                      queue_name=AGE_DIFFERENCE_FILTER_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=DATABASE_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.filter)

    def filter(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        id = data[0]

        if data[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            return

        if data[1] == CLOSE:
            body = ','.join([id, OK])
            self.terminator_queue.publish(body)
            logging.info('Sent %s' % body)
            return

        winner_age = int(data[5])
        loser_age = int(data[9])
        if winner_age - loser_age >= 20:
            winner_name = ' '.join([data[2], data[3]])
            loser_name = ' '.join([data[6], data[7]])
            result = '{}\t{}\t{}\t{}'.format(winner_age, winner_name, loser_age, loser_name)
            body = ','.join([id, result])
            self.out_queue.publish(body, ROUTING_KEY)
            logging.info('Sent %s' % body)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    filter = AgeDifferenceFilter()
    filter.run()
