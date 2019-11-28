#!/usr/bin/env python3

import logging
from glob import glob
from constants import END, RESPONSE_EXCHANGE, PLAYERS_EXCHANGE, MATCHES_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

PLAYERS_DATA = './data/atp_players.csv'
MATCHES_DATA = './data/atp_matches_*.csv'

class Client:
    def __init__(self):
        self.results = 0
        self.in_queue = RabbitMQQueue(exchange=RESPONSE_EXCHANGE, consumer=True,
                                      exclusive=True)
        self.players_queue = RabbitMQQueue(exchange=PLAYERS_EXCHANGE)
        self.matches_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE)

    def run(self):
        self.send_players_data()
        self.send_matches_data()
        self.in_queue.consume(self.print_response)

    def send_players_data(self):
        with open(PLAYERS_DATA, 'r') as file:
            file.readline()
            for line in iter(file.readline, ''):
                self.players_queue.publish(line)
                logging.info('Sent %s' % line)

        self.players_queue.publish(END)

    def send_matches_data(self):
        for filename in glob(MATCHES_DATA):
            with open(filename, 'r') as file:
                file.readline()
                for line in iter(file.readline, ''):
                    self.matches_queue.publish(line)
                    logging.info('Sent %s' % line)

        self.matches_queue.publish(END)

    def print_response(self, ch, method, properties, body):
        print(body.decode())
        self.results += 1
        if self.results == 3:
            self.in_queue.cancel()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)
    client = Client()
    client.run()
