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
START_SLEEP = 5 # max time to wait after starting a container to check
STARTING_TOLERANCE = 10 # tolerance for the first timeout
POLL_INTERVAL = 1 # docker polling interval
CLUSTER_CONFIG_YML = "cluster_config.yml"
MAXFAILS = 3 # max times to reattempt an operation (e.g. docker cmd)
MASTER_ROLE = "master"
SLAVE_ROLE = "slave"

def load_yaml():
    import yaml
    with open(CLUSTER_CONFIG_YML, 'r') as f:
            return yaml.safe_load(f)
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
        self.load_default_config()

    def run(self):
        logging.info("Starting Watchdog Logic")
        logging.info("Setting up queues")
        self.setup_queues()
        logging.info("Launching receiver thread")
        self.launch_receiver_thread()
        logging.info("Launching checker")
        self.launch_checker()

    def setup_queues(self):
        self.leader_queue = RabbitMQQueue(
            exchange=EXCHANGE, consumer=True)

    def load_default_config(self):
        self.default_config = load_yaml()

        self.last_timeout = {}
        for key in self.default_config.keys():
            if key == "client":
                continue
            structure_single_key = {
                "{}_{}".format(key,i):time.time()+STARTING_TOLERANCE
                for i in range(self.default_config[key])}
            self.last_timeout.update(structure_single_key)
            if key == "storage": # TODO
                self.storage_roles = {k: SLAVE_ROLE for k in structure_single_key.keys()}
                self.storage_master_heartbeat = 0 #instant timeout

        # Special structure to indicate that a container is being restarted and
        # should not be checked for timeouts.
        self.respawning = {k: False for k in self.last_timeout.keys()}

    def process_heartbeat(self, ch, method, properties, body):
        logging.debug("Received heartbeat message is {}".format(str(body)))
        data = body.decode().split(',')
        recv_hostname = data[1]
        recv_metadata = data[2]

        self.last_timeout[recv_hostname] = time.time()

        if recv_hostname.split("_")[0] == "storage":
            self.storage_roles[recv_hostname] = recv_metadata
            if self.storage_roles[recv_hostname] == MASTER_ROLE:
                self.storage_master_heartbeat = self.last_timeout[recv_hostname]

    def mkimgname(self, imgid):
        return "{}_{}_1".format(self.basedirname, imgid)

    def stop_container(self, imgid):
        imgid = self.mkimgname(imgid)
        failed = 0
        result = subprocess.run(['docker', 'stop', "-t" ,"1", imgid],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Stop command executed. Result={}. Output={}. Error={}'.format(
            result.returncode, result.stdout, result.stderr))
        while result.returncode != 0 and failed < MAXFAILED:
            failed +=1
            logging.error("Return code was not zero. Trying again.. ({}/{} attempts)".format(
                failed, MAXFAILED
            ))
            result = subprocess.run(['docker', 'stop', "-t" ,"1", imgid],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if failed >= MAXFAILED:
            raise Exception("Surpassed maximum retries for docker stop")


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
        return imgid in str(result.stdout)

    def respawn_container(self, imgid):
        logging.info("RESPAWN_CONTAINER called({})".format(imgid))
        try:
            self.stop_container(imgid)
            time.sleep(STOP_SLEEP)
            self.launch_container(imgid)
            launched = time.time()
            # poll to check if container is up
            while time.time() - launched < START_SLEEP and not container_is_running(imgid):
                time.sleep(POLL_INTERVAL)

            if time.time() - launched > START_SLEEP:
                raise Exception("Timeout while waiting for container {} to start".format(imgid))

            # Container started, now we need to be tolerant
            # for the first heartbeat, so:
            self.last_timeout[imgid] = time.time() + STARTING_TOLERANCE

        except Exception, e:
            logging.error("Exception on respawn_container: "+str(e))
        self.respawning[imgid] = False

    def launch_receiver_thread(self):
        self.leader_queue.async_consume(self.process_heartbeat, auto_ack=True)

    def reassign_storage_master(self):
        #TODO: what about the first time?all responding but no master => por esto el flag adicional y eso.

        # setear el master como slave y agarrar un nodo vivo
        current_time = time.time()
        for storage_node in self.storage_roles.keys():
            self.storage_roles[storage_node] = SLAVE_ROLE
            if current_time - self.last_timeout[storage_node] < HEARTBEAT_TIMEOUT:
                new_master = storage_node

        # TODO: mandarle mensaje

        while self.storage_roles[new_master] == SLAVE_ROLE:
            time.sleep(POLL_INTERVAL)

        self.reassigning = False
    def launch_checker(self):
        while True:
            #TODO: special case for storage master & replicas
            current_time = time.time()
            for hostname, last_heartbeat in self.last_timeout.items():
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT and not self.respawning[hostname]:
                    logging.info("Detected timeout of hostname {}".format(hostname))
                    self.respawning[hostname] = True

                    thread = threading.Thread(target=self.respawn_container, args=(hostname,))
                    thread.start()
                    current_time = time.time() #to prevent staleness

                    # TODO: check if is storage master
            if current_time - self.storage_master_heartbeat > HEARTBEAT_TIMEOUT and not self.reassigning:
                self.reassigning = True
                self.reassign_storage_master() # thread and shit
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    from leader import ElectableProcess
    from heartbeatprocess import HeartbeatProcess
    logging.basicConfig(level=logging.INFO)
    logging.info("Started watchdog!")
    hostname = os.getenv("HOSTNAME", "-1")
    pid = int(os.getenv("PID", -1))
    logging.info("Hostname is: {}, PID is {}".format(hostname, pid))

    config = load_yaml()
    pidlist = [n for n in range(config["watchdog"])
        if n != pid]

    def start_watchdog():
        wp = WatchdogProcess(hostname)
        wp.run()

    #proc = ElectableProcess(pid, pidlist, wp.run)
    hb = HeartbeatProcess.setup(ElectableProcess,
            pid, pidlist, start_watchdog)
    hb.run()
