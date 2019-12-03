#!/usr/bin/env python3

import logging
from constants import END, CLOSE, OK, OUT_JOINER_EXCHANGE, FILTERED_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

PLAYERS_DATA = 'atp_players.csv'
FILTERED_QUEUE = 'matches_join'
TERMINATOR_EXCHANGE = 'joiner_terminator'

class Joiner:
    def __init__(self):
        self.players = {}
        self.matches_queue = RabbitMQQueue(exchange=FILTERED_EXCHANGE, exchange_type='direct',
                                           consumer=True, queue_name=FILTERED_QUEUE,
                                           routing_keys=['joiner'])
        self.out_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE, exchange_type='direct')
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.save_players()
        self.matches_queue.consume(self.join)

    def save_players(self):
        with open(PLAYERS_DATA, 'r') as file:
            file.readline()
            for line in iter(file.readline, ''):
                data = line.split(',')
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
        self.out_queue.publish(body, 'filter')
        self.out_queue.publish(body, 'calculator')
        logging.info('Sent %s' % body)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)
    joiner = Joiner()
    joiner.run()
