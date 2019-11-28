#!/usr/bin/env python3

import pika

HOST = 'rabbitmq'

class RabbitMQQueue:
    def __init__(self, exchange, exchange_type='fanout', consumer=False, exclusive=False, queue_name='', routing_keys=[None]):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST))
        self.channel = connection.channel()

        self.exchange = exchange
        self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type)
        if not consumer:
            return

        result = self.channel.queue_declare(queue=queue_name, durable=True, exclusive=exclusive)
        self.queue_name = result.method.queue
        for routing_key in routing_keys:
            self.channel.queue_bind(exchange=exchange, queue=self.queue_name, routing_key=routing_key)

    def publish(self, body, routing_key=''):
        self.channel.basic_publish(exchange=self.exchange, routing_key=routing_key, body=body,
                                   properties=pika.BasicProperties(delivery_mode=2,))

    def consume(self, callback):
        self.tag = self.channel.basic_consume(queue=self.queue_name, auto_ack=True,
                                              on_message_callback=callback)
        self.channel.start_consuming()

    def cancel(self):
        self.channel.basic_cancel(self.tag)
