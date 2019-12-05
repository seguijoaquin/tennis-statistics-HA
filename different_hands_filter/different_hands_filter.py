#!/usr/bin/env python3

import pika
import logging
from constants import END, CLOSE, OK, OUT_JOINER_EXCHANGE
from rabbitmq_queue import RabbitMQQueue
from watchdog import heartbeatprocess

JOINED_QUEUE = 'joined_hands'
HANDS_EXCHANGE = 'hands'
TERMINATOR_EXCHANGE = 'hands_filter_terminator'
HANDS = ['R', 'L', 'U']

class DifferentHandsFilter:
    def __init__(self):
        self.acked = set()
        self.in_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE, exchange_type='direct',
                                      consumer=True, queue_name=JOINED_QUEUE,
                                      routing_keys=['filter'])
        self.out_queue = RabbitMQQueue(exchange=HANDS_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self, _):
        self.in_queue.consume(self.filter)

    def filter(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        id = data[0]

        if data[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if data[1] == CLOSE:
            if not id in self.acked:
                body = ','.join([data[0], OK])
                self.terminator_queue.publish(body)
                self.acked.add(id)
            else:
                self.in_queue.publish(body)
            logging.info('Sent %s' % body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        winner_hand = data[4]
        loser_hand = data[8]
        if winner_hand in HANDS and loser_hand != winner_hand:
            body = ','.join([id, '1'])
            self.out_queue.publish(body, winner_hand)
            logging.info('Sent %s to %s accumulator' % (body, winner_hand))
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    hb = heartbeatprocess.HeartbeatProcess.setup(DifferentHandsFilter)
    hb.run()
