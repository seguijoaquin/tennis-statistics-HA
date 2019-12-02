import logging
import time
import threading
import subprocess
import os

from rabbitmq_queue import RabbitMQQueue

EXCHANGE = "watchdogx"
CHECK_INTERVAL = 1
HEARTBEAT_TIMEOUT = 1.2
STOP_SLEEP = 5 # time to wait after stopping a container
START_SLEEP = 5 # time to wait after starting a container to check
STARTING_TOLERANCE = 10 # tolerance for the first timeout

class WatchdogProcess:
    """This process receives heartbeats from other containers
    and launches new instances when it detects that a process
    has failed.
    Since this particular process can be started while the
    cluster is already running, in case of a leader failure for
    example, it needs to know the a priori configuration
    of instances. It can be the case that there already are
    failed processes when this process starts."""
    def __init__(self, hostname):
        self.hostname = hostname
        self.basedirname  = os.getenv("BASEDIRNAME", "error")
        result = subprocess.run(['docker', 'images'],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('images command executed. Result={}. Output={}. Error={}'.format(
            result.returncode, result.stdout, result.stderr))
        self.load_default_config()
        self.setup_queues()
        self.launch_receiver_thread()
        self.launch_checker()

    def setup_queues(self):
        self.leader_queue = RabbitMQQueue(
            exchange=EXCHANGE, consumer=True)

    def load_default_config(self):
        import yaml
        with open("cluster_config.yml", 'r') as f:
            self.default_config = yaml.safe_load(f)

        self.last_timeout = {}
        for key in self.default_config.keys():
            structure_single_key = {
                "{}_{}".format(key,i):time.time()+STARTING_TOLERANCE
                for i in range(self.default_config[key])}
            self.last_timeout.update(structure_single_key)
        del self.last_timeout[self.hostname]
        # Special structure to indicate that a container is being restarted and
        # should not be checked for timeouts.
        self.respawning = {k: False for k in self.last_timeout.keys()}
        # TODO: special case for storage (master & replicas)

    def process_heartbeat(self, ch, method, properties, body):
        data = body.decode().split(',')
        recv_hostname = data[1]
        recv_metadata = data[2]

        self.last_timeout[recv_hostname] = time.time()

        # TODO: if hostname is compatible with storage then check the metadata

    def mkimgname(self, imgid):
        return "{}_{}_1".format(self.basedirname, imgid)
    def stop_container(self, imgid):
        imgid = self.mkimgname(imgid)
        result = subprocess.run(['docker', 'stop', "-t" ,"1", imgid],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Stop command executed. Result={}. Output={}. Error={}'.format(
            result.returncode, result.stdout, result.stderr))

    def launch_container(self, imgid):
        imgid = self.mkimgname(imgid)
        cmd = ['docker', 'start', imgid]
        result = subprocess.run(
            cmd,
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Start command executed. CMD={} Result={}. Output={}. Error={}'.format(
            " ".join(cmd), result.returncode, result.stdout, result.stderr))

    def container_is_running(self, imgid):
        result = subprocess.run(['docker', 'ps'],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('PS command executed. Result={}. Output={}. Error={}'.format(
            result.returncode, result.stdout, result.stderr))

        return imgid in str(result.stdout)

    def respawn_container(self, imgid):
        logging.info("RESPAWN_CONTAINER called({})".format(imgid))
        self.stop_container(imgid)
        time.sleep(STOP_SLEEP)
        self.launch_container(imgid)
        time.sleep(START_SLEEP)
        if not self.container_is_running(imgid):
            logging.warn("Image {} was started but was not found in ps!".format(imgid))
        self.respawning[imgid] = False

    def launch_receiver_thread(self):
        self.leader_queue.async_consume(self.process_heartbeat)

    def launch_checker(self):
        while True:
            #TODO: special case for storage master & replicas
            current_time = time.time()
            for hostname, last_heartbeat in self.last_timeout.items():
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT and not self.respawning[hostname]:
                    self.respawning[hostname] = True
                    thread = threading.Thread(target=self.respawn_container, args=(hostname,))
                    thread.start()
                    current_time = time.time() #to prevent staleness
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)
    logging.info("Started watchdog!")
    hostname = os.getenv("HOSTNAME", "-1")
    logging.info("Hostname is: {}".format(hostname))
    proc = WatchdogProcess(hostname)