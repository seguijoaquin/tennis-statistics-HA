#!/usr/bin/env python3

import logging, sys, getopt
from glob import glob
from uuid import uuid1
from constants import END, RESPONSE_EXCHANGE, MATCHES_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

MATCHES_DATA = './data/atp_matches_*.csv'
FROM_DEFAULT = '20000101'
TO_DEFAULT = '20200101'

class Client:
    def __init__(self, argv):
        self.id = str(uuid1())
        self.metadata = [FROM_DEFAULT, TO_DEFAULT, self.id]
        self.parse_args(argv)
        self.results = 0
        self.in_queue = RabbitMQQueue(exchange=RESPONSE_EXCHANGE + ':' + self.id,
                                      consumer=True, exclusive=True)
        self.matches_queue = RabbitMQQueue(exchange=MATCHES_EXCHANGE)

    def parse_args(self, argv):
        try:
            options, args = getopt.getopt(argv,"f:t:",["from=", "to="])
        except getopt.GetoptError:
            print("Usage: python3 client.py [--from=YYYYMMDD] [--to=YYYYMMDD]")
            sys.exit(2)

        for option, arg in options:
            if option in ("-f", "--from"):
                self.metadata[0] = arg
            else:
                self.metadata[1] = arg

    def run(self):
        self.send_matches_data()
        self.in_queue.consume(self.print_response)

    def send_matches_data(self):
        for filename in glob(MATCHES_DATA):
            with open(filename, 'r') as file:
                file.readline()
                for line in iter(file.readline, ''):
                    body = ','.join(self.metadata) + ',' + line
                    self.matches_queue.publish(body)
                    logging.info('Sent %s' % body)

        end = ','.join([self.id, END])
        self.matches_queue.publish(end)
        logging.info('Sent %s' % end)

    def print_response(self, ch, method, properties, body):
        print(body.decode())
        self.results += 1
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if self.results == 3:
            self.in_queue.cancel()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)
    client = Client(sys.argv[1:])
    client.run()
