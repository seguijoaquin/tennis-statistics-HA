#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, OUT_AGE_CALCULATOR_EXCHANGE, DATABASE_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
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
        if body == END_ENCODED:
            self.terminator_queue.publish(END)
            return

        if body == CLOSE_ENCODED:
            self.terminator_queue.publish(OK)
            self.in_queue.cancel()
            return

        data = body.decode().split(',')
        winner_age = int(data[4])
        loser_age = int(data[8])
        if winner_age - loser_age >= 20:
            winner_name = ' '.join([data[1], data[2]])
            loser_name = ' '.join([data[5], data[6]])
            result = '{}\t{}\t{}\t{}'.format(winner_age, winner_name, loser_age, loser_name)
            self.out_queue.publish(result, ROUTING_KEY)
            logging.info('Sent %s' % result)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    filter = AgeDifferenceFilter()
    filter.run()
