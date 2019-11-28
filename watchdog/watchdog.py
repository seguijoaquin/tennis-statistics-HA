import logging
import time
import threading

from rabbitmq_queue import rabbitmq_queue

EXCHANGE = "watchdogx"
CHECK_INTERVAL = 1
HEARTBEAT_TIMEOUT = 1.2

class WatchdogProcess:
    """This process receives heartbeats from other containers
    and launches new instances when it detects that a process
    has failed.
    Since this particular process can be started while the
    cluster is already running, in case of a leader failure for
    example, it needs to know the a priori configuration
    of instances. It can be the case that there already are
    failed processes when this process starts."""
    def __init__(self):
        self.load_default_config()
        self.setup_queues()
        self.launch_receiver_thread()
        self.launch_checker()

    def setup_queues(self):
        self.leader_queue = RabbitMQQueue(
            exchange=EXCHANGE, consumer=True)

    def load_default_config(self):
        with open("cluster_config.yml", 'r') as f:
            self.default_config = yaml.safe_load(stream)

        # TODO: initiate structure mapping
        # hostname => last heartbeat
        # special case for storage (master & replicas)

    def process_heartbeat(self, ch, method, properties, body):
        data = body.decode().split(',')
        recv_hostname = data[1]
        recv_metadata = data[2]

        # TODO: handle hostname type
        # if hostname is compatible with storage then check the metadata

    def launch_receiver_thread(self):
        self.receiver_thread = threading.Thread(target=self.process_heartbeat)

    def launch_checker(self):
        while True:
            #TODO: check that we have a recent heartbeat of all processes
            #special case for storage master & replicas
            time.sleep(CHECK_INTERVAL)