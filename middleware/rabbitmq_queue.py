#!/usr/bin/env python3

import pika
import threading
import time
import logging
HOST = 'rabbitmq'

class RabbitMQQueue:
    def __init__(self, exchange, exchange_type='fanout', consumer=False, exclusive=False, queue_name='', routing_keys=[None]):
        self.thread_stop = True
        self.thread = None
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, heartbeat=0))
        self.channel = connection.channel()

        self.exchange = exchange
        self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)
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
        self.tag = self.channel.basic_consume(queue=self.queue_name, auto_ack=False,
                                              on_message_callback=callback)
        self.channel.start_consuming()

    def async_consume(self, callback):
        """Start a thread and consume messages there.
        Invariant: no more than one thread is consuming in an object
        instance."""
        logging.info("Async consume")
        if self.thread is not None:
            return
        self.thread_stop = False

        def wrapped_callback(ch, method, properties, body):
            #logging.info("Wrapped callback'd")
            callback(ch, method, properties, body)
            #if not self.thread_stop:
            #   callback(ch, method, properties, body)
            #else:
            #    print("Should stop now!")
            #    callback(ch, method, properties, body)
            #    self.channel.basic_cancel(self.tag)
            #    exit

        self.thread = threading.Thread(target=self.consume, args=(wrapped_callback,))
        self.thread.start()

    def cancel(self):
        self.channel.basic_cancel(self.tag)
