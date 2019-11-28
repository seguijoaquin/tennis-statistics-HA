#!/usr/bin/env python3

import pika
import logging
from constants import END, CLOSE, OK, OUT_JOINER_EXCHANGE, MATCHES_EXCHANGE, PLAYERS_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
MATCHES_QUEUE = 'matches_join'
TERMINATOR_EXCHANGE = 'joiner_terminator'

class Joiner:
    def __init__(self):
        self.players = {}
        self.matches_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE, consumer=True,
                                           queue_name=MATCHES_QUEUE)
        self.players_queue = RabbitMQQueue(exchange=PLAYERS_EXCHANGE, consumer=True,
                                           exclusive=True)
        self.out_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE)
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.players_queue.consume(self.save_player)
        self.matches_queue.consume(self.join)

    def save_player(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        if body == END_ENCODED:
            self.players_queue.cancel()
            return

        data = body.decode().split(',')
        self.players[data[0]] = data[1:5]

    def join(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        if body == END_ENCODED:
            self.terminator_queue.publish(END)
            return

        if body == CLOSE_ENCODED:
            self.terminator_queue.publish(OK)
            self.matches_queue.cancel()
            return

        data = body.decode().split(',')
        winner_id = data[4]
        loser_id = data[5]
        data = [data[2]] + self.players[winner_id] + self.players[loser_id]
        body = ','.join(data)
        self.out_queue.publish(body)
        logging.info('Sent %s' % body)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)
    joiner = Joiner()
    joiner.run()
