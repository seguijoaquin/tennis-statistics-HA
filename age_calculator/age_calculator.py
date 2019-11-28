#!/usr/bin/env python3

import logging
from datetime import datetime
from constants import END, OK, CLOSE, OUT_JOINER_EXCHANGE, OUT_AGE_CALCULATOR_EXCHANGE
from rabbitmq_queue import RabbitMQQueue

END_ENCODED = END.encode()
CLOSE_ENCODED = CLOSE.encode()
AGE_CALCULATOR_QUEUE = 'joined_age'
TERMINATOR_EXCHANGE = 'calculator_terminator'

class AgeCalculator:
    def __init__(self):
        self.in_queue = RabbitMQQueue(exchange=OUT_JOINER_EXCHANGE, consumer=True,
                                      queue_name=AGE_CALCULATOR_QUEUE)
        self.out_queue = RabbitMQQueue(exchange=OUT_AGE_CALCULATOR_EXCHANGE)
        self.terminator_queue = RabbitMQQueue(exchange=TERMINATOR_EXCHANGE)

    def run(self):
        self.in_queue.consume(self.calculate)

    def calculate(self, ch, method, properties, body):
        logging.info('Received %r' % body)
        if body == END_ENCODED:
            self.terminator_queue.publish(END)
            return

        if body == CLOSE_ENCODED:
            self.terminator_queue.publish(OK)
            self.in_queue.cancel()
            return

        data = body.decode().split(',')
        tourney_date = data[0]
        winner_birthdate = data[4]
        loser_birthdate = data[8]
        if winner_birthdate == '' or loser_birthdate == '':
            return

        tourney_date = datetime.strptime(tourney_date, '%Y%m%d')
        winner_age = self._compute_age(datetime.strptime(winner_birthdate, '%Y%m%d'), tourney_date)
        loser_age = self._compute_age(datetime.strptime(loser_birthdate, '%Y%m%d'), tourney_date)
        data[4] = str(winner_age)
        data[8] = str(loser_age)
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
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)

    calculator = AgeCalculator()
    calculator.run()
