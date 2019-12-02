import logging
import time
from rabbitmq_queue import RabbitMQQueue
import threading
from watchdog import watchdog

HEARTBEAT_INTERVAL = watchdog.HEARTBEAT_TIMEOUT/3

class HeartbeatProcess:
    """This class factorizes the heartbeat protocol.
    Receives a hostname, some metadata and a callback.
    Starts a thread sending heartbeats to the watchdog exchange
    and then calls the callback to execute business logic.
    Metadata can be used to provide additional information to the
    watchdog, such as the specific role the process currently has.

    Therefore the callback also receives this object, so it can
    change the metadata when it changes its role during runtime.

    Parameters
    ----------
    hostname: string
    metadata: string
        A string without commas so that it can be passed during heartbeat.
    callback: function
        Receives this object as argument. Useful for altering metadata
        during runtime."""
    def __init__(self, hostname, metadata, callback):
        logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.ERROR)
        logging.info("Instancing heartbeat process for hostname {}".format(hostname))
        self.hostname = hostname
        self.metadata = metadata
        self.callback = callback
        logging.basicConfig(format='%(asctime)s [PID {}] %(message)s'.format(self.hostname))
        self.exchange = RabbitMQQueue(
            exchange=watchdog.EXCHANGE,
            consumer=False, exchange_type="fanout")

    def start_heartbeat_thread(self):
        logging.info("Starting heartbeat thread..")
        self.thread = threading.Thread(target=self.periodic_heartbeat)
        self.thread.start()
    def periodic_heartbeat(self):
        while True:
            logging.info("Sending hearbeat")
            self.exchange.publish("heartbeat,{},{}".format(self.hostname, self.metadata))
            time.sleep(HEARTBEAT_INTERVAL)

    def run(self):
        """Starts the thread and runs the callback"""
        logging.info("Starting thread and running the callback")
        self.start_heartbeat_thread()
        self.callback(self)