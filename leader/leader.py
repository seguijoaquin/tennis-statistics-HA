import os
import logging
import time
import threading
from rabbitmq_queue import RabbitMQQueue

HEARTBEAT_INTERVAL = 0.3
TIMEOUT_HEARTBEAT = 3*HEARTBEAT_INTERVAL
TIMEOUT_TRANSFER = 0.5
TIMEOUT_PROCESS = 2
TIMEOUT_ANSWER = 2*TIMEOUT_TRANSFER + TIMEOUT_PROCESS
# In Coulouris(2011) the length of the  timeout while waiting
# for a COORDINATOR message after the process received an
# ANSWER is not specified. By means of a simple sequence
# diagram it becomes clear that the timeout must be longer
# than the ANSWER timeout, in case the other process
# is waiting for an ANSWER. Therefore it seems straightforward
# to set it so:
TIMEOUT_COORD = 2*TIMEOUT_ANSWER

ELECTION_EXCHANGE = "electx"
LEADER_EXCHANGE = "leaderx"

class ElectableProcess:
    """This class factorizes the leader election protocol.
    When this process is chosen as a leader this class
    runs callback on a separate thread."""
    def __init__(self, pid, pid_list, callback):
        """Starts the election protocol. Receives this
        process' pid number, a list of other pids
        and a callback function used when this process is
        elected."""
        self.pid = pid
        self.pid_list = pid_list
        self.onleader_callback = callback
        logging.basicConfig(format='%(asctime)s [PID {}] %(message)s'.format(self.pid))

    def run(self, _):
        self.setup_queues()
        logging.info("Waiting 5s for starting everything..")
        time.sleep(5)
        self.start_election()

    def setup_queues(self):
        self.exchange = RabbitMQQueue(
            exchange=ELECTION_EXCHANGE, consumer=False, exchange_type="direct")
        self.process_queue = RabbitMQQueue(
            exchange=ELECTION_EXCHANGE, consumer=True, exchange_type="direct",
                routing_keys=[str(self.pid)])
        self.leader_ex = RabbitMQQueue(
            exchange=LEADER_EXCHANGE, consumer=False)
        self.leader_queue = RabbitMQQueue(
            exchange=LEADER_EXCHANGE, consumer=True)

    def process_message(self, ch, method, properties, body):
        data = body.decode().split(',')
        logging.info("Received {}".format(body.decode()))
        if data[0] == "election":
            logging.info("Sending answer,{} to {}".format(self.pid, data[1]))
            self.exchange.publish("answer,{}".format(self.pid), data[1])
        elif data[0] == "answer":
            self.received_answer = True # atomic
        elif data[0] == "coordinator":
            self.leader = int(data[1]) # atomic

    def start_election(self):
        self.received_answer = False
        self.leader = None

        logging.info("Starting election -- sending ELECTION")
        for remote_pid in self.pid_list:
            if remote_pid > self.pid:
                logging.info("Sending election,{} to {}".format(self.pid, remote_pid))
                self.exchange.publish("election,{}".format(self.pid), str(remote_pid))

        # If we do not receive an answer within the timeout,
        # we are now the coordinator.
        # This processes requests in another thread,

        logging.info("Consuming from queue")

        self.process_queue.async_consume(self.process_message)

        logging.info("Sleeping for {}s".format(TIMEOUT_ANSWER))
        time.sleep(TIMEOUT_ANSWER)
        logging.info("Woke up from timeout")

        if self.received_answer:
            logging.info("Answer received!")
            time.sleep(TIMEOUT_COORD)
            logging.info("Woke up from coord timeout")
            # same as before => factorize in a function?
            if self.leader is None:
                logging.info("NO leader still! Rebooting election")
                self.start_election()
            logging.info("NEW leader! id is: {}".format(self.leader))
        else:
            logging.info("NO answer received! Therefore I am the leader. Sending coord.")
            # No answer received in timeout, therefore this process is leader
            for remote_pid in self.pid_list:
                if remote_pid < self.pid:
                    logging.info("->coordinator,{} to key {}".format(self.pid, str(remote_pid)))
                    self.exchange.publish("coordinator,{}".format(self.pid), str(remote_pid))
            logging.info("Setting leader pid")
            self.leader = self.pid


        if self.leader == self.pid:
            logging.info("Starting leader logic in this process")
            self.start_leader()
        else:
            logging.info("Following leader...")
            self.follow_leader()

    def start_leader(self):
        self.logic_thread = threading.Thread(target=self.onleader_callback)
        self.logic_thread.start()
        # set up leader heartbeat
        while True:
            self.leader_ex.publish("heartbeat")
            time.sleep(HEARTBEAT_INTERVAL)

    def process_heartbeat(self, ch, method, properties, body):
        self.last_heartbeat = time.time()

    def follow_leader(self):
        # in another process update the counter with the time
        # this one just wakes up every fraction of a second updating
        # the count
        self.last_heartbeat = time.time() - 0.01
        self.leader_queue.async_consume(self.process_heartbeat)
        diff = time.time() - self.last_heartbeat

        while diff < TIMEOUT_HEARTBEAT:
            #logging.info("Sleeping for {}s".format(TIMEOUT_HEARTBEAT - diff + 0.1))
            time.sleep(TIMEOUT_HEARTBEAT - diff + 0.1) # So we don't over-wait
            diff = time.time() - self.last_heartbeat

        logging.info("Timed out leader. About to start a new election")
        self.start_election()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)
    logging.info("Started!")
    import socket
    logging.info("Host is: {}".format(socket.gethostname()))
    pid = int(os.getenv("PID", -1))
    logging.info("Pid is: {}".format(pid))
    pids = [i for i in range(1,4) if i != pid]
    proc = ElectableProcess(pid, pids, print)

print("Called!!")