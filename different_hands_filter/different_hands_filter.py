#!/usr/bin/env python3

import pika
import logging
from constants import END, CLOSE, OK, OUT_JOINER_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
JOINED_QUEUE = 'joined_hands'
HANDS_EXCHANGE = 'hands'
TERMINATOR_EXCHANGE = 'hands_filter_terminator'
HANDS = ['R', 'L', 'U']

class DifferentHandsFilter:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE, consumer=True,
                                      queue_name=JOINED_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=HANDS_EXCHANGE, exchange_type='direct')
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
        winner_hand = data[3]
        loser_hand = data[7]
        if winner_hand in HANDS and loser_hand != winner_hand:
            self.out_queue.publish('1', winner_hand)
            logging.info('Sent 1 to %s accumulator' % winner_hand)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    filter = DifferentHandsFilter()
    filter.run()
