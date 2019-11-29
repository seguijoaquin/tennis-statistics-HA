#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, OUT_JOINER_EXCHANGE, FILTERED_EXCHANGE, PLAYERS_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
FILTERED_QUEUE = 'matches_join'
TERMINATOR_EXCHANGE = 'joiner_terminator'

class Joiner:
    def __init__(self):
        self.players = {}
        self.players_queue = RabbitMQQueue(exchange=PLAYERS_EXCHANGE, consumer=True,
                                           exclusive=True)
        self.matches_queue = RabbitMQQueue(exchange=FILTERED_EXCHANGE, consumer=True,
                                           queue_name=FILTERED_QUEUE)
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

        winner_id = data[5]
        loser_id = data[6]
        data = [data[0], data[3]] + self.players[winner_id] + self.players[loser_id]
        body = ','.join(data)
        self.out_queue.publish(body)
        logging.info('Sent %s' % body)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)
    joiner = Joiner()
    joiner.run()
