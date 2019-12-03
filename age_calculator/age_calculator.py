#!/usr/bin/env python3

import logging
from datetime import datetime
from constants import END, OK, CLOSE, OUT_JOINER_EXCHANGE, OUT_AGE_CALCULATOR_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

AGE_CALCULATOR_QUEUE = 'joined_age'
TERMINATOR_EXCHANGE = 'calculator_terminator'

class AgeCalculator:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE, exchange_type='direct',
                                      consumer=True, queue_name=AGE_CALCULATOR_QUEUE,
                                      routing_keys=['calculator'])
        self.out_queue = RabbitMQQueue(exchange=OUT_AGE_CALCULATOR_EXCHANGE)
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        data = body.decode().split(',')
        id = data[0]

        if data[1] == END:
            self.terminator_queue.publish(body)
            logging.info('Sent %r' % body)
            return

        if data[1] == CLOSE:
            body = ','.join([data[0], OK])
            self.terminator_queue.publish(body)
            logging.info('Sent %s' % body)
            return

        tourney_date = data[1]
        winner_birthdate = data[5]
        loser_birthdate = data[9]
        if winner_birthdate == '' or loser_birthdate == '':
            return

        tourney_date = datetime.strptime(tourney_date, '%Y%m%d')
        winner_age = self._compute_age(datetime.strptime(winner_birthdate, '%Y%m%d'), tourney_date)
        loser_age = self._compute_age(datetime.strptime(loser_birthdate, '%Y%m%d'), tourney_date)
        data[5] = str(winner_age)
        data[9] = str(loser_age)
        body = ','.join(data)
        self.out_queue.publish(body)
        logging.info('Sent %s' % body)

    def _compute_age(self, birthdate, tourney_date):
        years = tourney_date.year - birthdate.year
        if tourney_date.month < birthdate.month or \
           (tourney_date.month == birthdate.month and tourney_date.day < birthdate.day):
            years -= 1
        return years

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.ERROR)

    calculator = AgeCalculator()
    calculator.run()
