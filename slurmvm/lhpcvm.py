#!/usr/bin/python
"""
LHPC VM management module

Contains classes for managing running VM resources
"""

import os, pwd, fcntl, json
import sys, subprocess, pickle, socket, time
import logging as log
import configparser


from filelock import Timeout, FileLock

class SlurmVMConfig(object):
    def __init__(self):

        self.__default_config_file = "/etc/slurm/lhpcvm.conf"
        self.__fallback_config_file = "lhpcvm.conf"
        self.__used_config_file = ""
        self.xen_server_hostname = "localhost"
        self.log_level="DEBUG"
        self.snapshot_prefix="ss"
        self.use_snapshot = False
        self.vm_dict = {}

        self.config_valid = False

        self.__read_config()

    def __read_config(self):

        self.config_valid = False

        if os.path.exists(self.__default_config_file):
            self.__used_config_file = self.__default_config_file
        else:
            print("Configuration file not found at: %s" % self.__default_config_file )
        
        if self.__used_config_file == "":
            if os.path.exists(self.__fallback_config_file):
                self.__used_config_file = self.__fallback_config_file
            else:
                print("Configuration file not found at: %s" % self.__fallback_config_file )

        if self.__used_config_file == "":
            self.config_valid = False
            return

        if self.__used_config_file!="":
            try:
                self.config = configparser.ConfigParser()
                print("Reading", self.__used_config_file)
                self.config.read(self.__used_config_file)
            except:
                print("Couldn't parse configuration file at /etc/slurm/lhpcvm.conf")
                return
        else:
            return

        default_params = self.config.defaults()

        if "xenserverhost" in default_params:
            self.xen_server_hostname = self.config.get("DEFAULT", "xenserverhost")

        if "loglevel" in default_params:
            self.log_level = self.config.get("DEFAULT", "loglevel")

        if "snapshotprefix" in default_params:
            self.snapshot_prefix = self.config.get("DEFAULT", "snapshotprefix")

        if "use_snapshot" in default_params:
            value = self.config.get("DEFAULT", "use_snapshot")
            if value == "yes":
                self.use_snapshot = True
            else:
                self.use_snapshot = False

        self.vm_dict = {}

        for vm in self.config.sections():
            options = self.config.options(vm)

            vm_name = ""
            vm_hostname = ""

            if "name" in options:
                vm_name = self.config.get(vm, "name")

            if "hostname" in options:
                vm_hostname = self.config.get(vm, "hostname")

            if vm_name!="" and vm_hostname!="":
                self.vm_dict[vm_name] = vm_hostname

        self.config_valid = True

    def show_config(self):
        print("XenServer host  :", self.xen_server_hostname)
        print("Log level       :", self.log_level)
        print("Snapshot prefix :", self.snapshot_prefix)
        print("Using snapshot  :", self.use_snapshot)
        print()
        print("Configured VM:s:")
        for vm in self.vm_dict.keys():
            print("VM:", vm, "ip =", self.vm_dict[vm])

        if self.config_valid:
            print("Configuration is valid.")
        else:
            print("Configuration is not valid.")



class Singleton(object):
    """Singleton mixin class"""
    _instance = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

class PortProber(object):
    """Class for probing ports"""
    def __init__(self, hostname="", timeout=1):
        """Class constructor"""
        
        self.hostname = hostname
        self.timeout = timeout

    def is_port_open(self, port):
        """Probe a port on a host

        Probes for self.timeout amount of time.

        Returns True if port is open otherwise False"""

        #server_ip = socket.gethostbyname(self.hostname)
        server_ip = self.hostname

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((server_ip, port))
            if result == 0:
                return True
            else:
                return False
            sock.close()

        except socket.timeout:
            log.error("Connection timed out to %s." % server_ip)
            return False

        except KeyboardInterrupt:
            log.error("You pressed Ctrl+C")
            return False

        except socket.gaierror:
            log.error('Hostname %s could not be resolved. Exiting' % server_ip)
            return False

        except socket.error:
            log.error("Couldn't connect to server %s." % server_ip )
            return False

class XenServer(object):
    """Class for controlling a XenServer Hypervisor"""
    def __init__(self, hostname, dryrun=False):
        self.hostname = hostname
        self.dryrun = dryrun

    def exec_cmd(self, cmd):
        """Execute a command and return output"""
        output = subprocess.check_output(cmd, shell=True)
        return output.decode('ascii')

    def xe(self, cmd):
        """Execute a xe command on the XenServer"""
        log.debug("XenServer.xe(%s)" % cmd)

        return self.exec_cmd("ssh %s 'xe %s'" % (self.hostname, cmd))
    
    def vm_list(self):
        """Return a dict of vm:s"""

        log.debug("XenServer.vm_list()")

        output = self.xe("vm-list")

        lines = output.split("\n")

        vm_dict = {}

        for line in lines:
            if "uuid" in line:
                vm_uuid = line.split(":")[1].strip()
            if "name-label" in line:
                vm_name = line.split(":")[1].strip()
            if "power-state" in line:
                vm_state = line.split(":")[1].strip()
                vm_dict[vm_name] = {"uuid": vm_uuid, "state": vm_state}

        return vm_dict

    def is_vm_running(self, vm_name):
        """Check if a vm is running"""

        log.debug("XenServer.is_vm_running(%s)" % vm_name)

        vm_dict = self.vm_list()
        
        if vm_name in vm_dict:
            log.debug("vm in dict with state: %s" % vm_dict[vm_name]["state"])
            return vm_dict[vm_name]["state"] == "running"
        else:
            log.debug("vm not found in vm_list.")
            return False

    def vm_start(self, vm_name):
        """Start a named vm"""

        log.debug("XenServer.vm_start(%s)" % vm_name)

        output = self.xe("vm-start vm=%s" % vm_name)
        log.debug(output)

    def vm_shutdown(self, vm_name):
        """Shutdown a named vm"""
        
        log.debug("vm_shutdown(%s)" % vm_name)

        output = self.xe("vm-shutdown vm=%s" % vm_name)
        log.debug(output)

    def vm_snapshot(self, vm_name, snapshot_name):
        """Take a snapshot of named vm"""
        log.debug("XenServer.vm_shapshot(%s, %s)" % (vm_name, snapshot_name))

        output = self.xe('vm-snapshot new-name-label=%s vm=%s' % (snapshot_name, vm_name))

    def vm_snapshot_revert(self, vm_name, snapshot_name):
        """Revert to a named snapshot"""

        log.debug("XenServer.vm_shapshot_revert(%s, %s)" % (vm_name, snapshot_name))

        snapshots = self.snapshot_list()

        ss_uuid = snapshots[snapshot_name]["uuid"]

        self.xe("snapshot-revert snapshot-uuid=%s" % (ss_uuid))

    def snapshot_list(self):
        """Return a dict of snapshots"""

        log.debug("XenServer.snapshot_list()")

        output = self.xe("snapshot-list")

        lines = output.split("\n")

        snapshot_dict = {}

        for line in lines:
            if "uuid" in line:
                snapshot_uuid = line.split(":")[1].strip()
            if "name-label" in line:
                snapshot_name = line.split(":")[1].strip()
                snapshot_dict[snapshot_name] = {"uuid": snapshot_uuid, "state": snapshot_name}

        return snapshot_dict


class VMTracker(object): 
    """Class for tracking running vm:s"""

    def __init__(self, slurm_vm_config):
        #Singleton.__init__(self)

        self.slurm_vm_config = slurm_vm_config
        self.idle_list = []
        self.running_dict = {}
        self.user_id = 0
        self.group_id = 0
        self.home_dir = ""

        # --- Filenames for tracker db and lockfile

        self.state_filename = "tracker.state"
        self.state_lock_filename = "tracker.state.lck"

        # --- Create file locking object

        self.lock = FileLock(self.state_lock_filename, timeout=1)

        # --- Create or read state file

        self.create()

    def create(self):
        """Create or load tracker database"""

        log.debug("VMTracker.create()")

        if not os.path.exists(self.state_filename):
            log.debug("No tracker state found. Creating.")
            self.init_tracker()
            with open(self.state_filename, "wb+") as f:
                tmp_dict = self.__dict__.copy()
                del tmp_dict["lock"]
                pickle.dump(tmp_dict, f)

        else:
            log.debug("Tracker state found. Loading.")
            with self.lock:
                with open(self.state_filename, "rb+") as f:
                    tmp_dict = pickle.load(f)
                    lock = self.lock
                    self.__dict__.clear()
                    self.__dict__.update(tmp_dict)
                    self.lock = lock

    def save(self):
        """Save current database to disk"""

        log.debug("VMTracker.save()")

        with self.lock:
            with open(self.state_filename, "wb+") as f:
                tmp_dict = self.__dict__.copy()
                del tmp_dict["lock"]
                pickle.dump(tmp_dict, f)

    def add_vm(self, name, hostname):
        """Add a vm to list of resources."""

        log.debug("VMTracker.add_vm(%s, %s)" % (name, hostname))

        self.idle_list.append([name, hostname])

    def init_tracker(self):
        """Initialise initial resources."""

        log.debug("VMTracker.init_tracker()")

        vm_dict = self.slurm_vm_config.vm_dict

        for vm in vm_dict.keys():
            log.debug("Adding VM " + vm + "(" + vm_dict[vm] + ") to initial configuration.")
            self.add_vm(vm, vm_dict[vm])

    def aquire_vm(self, job_id):
        """Aquire a vm for a specific job_id"""

        log.debug("VMTracker.aquire_vm(%s)" % job_id)

        if len(self.idle_list)>0:
            vm_info = self.idle_list.pop()
            self.running_dict[job_id] = [vm_info[0], vm_info[1]]
            self.save()
            return vm_info[0], vm_info[1]
        else:
            return "", ""

    def release_vm(self, job_id):
        """Release a vm from a job_id"""

        log.debug("VMTracker.release_vm(%s)" % job_id)

        if job_id in self.running_dict:
            vm_info = self.running_dict.pop(job_id)
            self.add_vm(vm_info[0], vm_info[1])
            self.save()
            return vm_info[0], vm_info[1]
        else:
            return "", ""

    def has_user_store(self):
        """Return state of user store directory"""

        log.debug("VMTracker.has_user_store()")

        self.store_dir = os.path.join(self.home_dir, ".lhpc")
        return os.path.exists(self.store_dir)

    def setup_user_store(self):
        """Setup user store directory with correct permissions"""

        log.debug("VMTracker.setup_user_store()")

        if not self.has_user_store():
            log.debug("Creating user store directory.")
            os.mkdir(self.store_dir)
            os.chown(self.store_dir, self.user_id, self.group_id)
            os.chmod(self.store_dir, 0o700)

    def user_store_dir(self):
        """Return user store directory"""

        log.debug("VMTracker.user_store_dir()")

        if not self.has_user_store():
            self.setup_user_store()
        return self.store_dir

    def write_job_hostfile(self, job_id, vm_host):
        """Write job host file containing ip of running VM"""

        log.debug("VMTracker.write_job_hostfile(%s, %s)" % (job_id, vm_host))

        store_dir = self.user_store_dir()
        job_host_filename = os.path.join(store_dir, "vm_host_%s.ip" % job_id.strip())

        log.debug("Creating job ip-file: " + job_host_filename)

        with open(job_host_filename, "w") as f:
            f.write(vm_host+"\n")

        os.chown(job_host_filename, self.user_id, self.group_id)
        os.chmod(job_host_filename, 0o700)

    def remove_job_hostfile(self, job_id, vm_host):
        """Remove a job host file when not needed anymore"""

        log.debug("VMTracker.remove_job_hostfile(%s, %s)" % (job_id, vm_host))

        store_dir = self.user_store_dir()
        job_host_filename = os.path.join(store_dir, "vm_host_%s.ip" % job_id.strip())

        log.debug("Removing job ip-file: "+job_host_filename)

        if os.path.exists(job_host_filename):
            os.remove(job_host_filename)

    def status(self):
        """Print status of data base"""

        log.debug("VMTracker.status()")

        log.debug("Idle VMs:")
    
        for idle_vm in self.idle_list:
            log.debug(idle_vm)
    
        log.debug("Jobs with running VMs:")

        for job_id in self.running_dict.keys():
            log.debug(job_id + " " + str(self.running_dict[job_id]))


if __name__ == "__main__":

    # --- Configure logging - All messages from prolog/epilog uses Python logging.

    root = log.getLogger()
    root.setLevel(log.DEBUG)

    handler = log.StreamHandler(sys.stdout)
    handler.setLevel(log.DEBUG)
    formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # prober = PortProber("10.18.50.22")

    # timeout = 60
    
    # while not prober.is_port_open(3389) and timeout > 0:
    #     log.info("Still waiting for host %s to become available..." % ("10.18.50.22"))
    #     time.sleep(1)
    #     timeout -= 1

    # sys.exit(0)

    slurm_vm_config = SlurmVMConfig()

    if slurm_vm_config.config_valid:
        slurm_vm_config.show_config()
    else:
        print("No valid config file.")

    vm_tracker = VMTracker(slurm_vm_config)
    vm_tracker.status()

    sys.exit(0)

    print()
    print("Querying XenServer...")
    print()

    xen = XenServer(slurm_vm_config.xen_server_hostname)
    vm_dict = xen.vm_list()

    for vm in vm_dict.keys():
        print(vm)
        print("\t",vm_dict[vm]["uuid"])
        print("\t",vm_dict[vm]["state"])

    vm_name = "win10m-ip22"
    vm_host = "10.18.50.22"

    sys.exit(0)

    print()
    print("Starting:", vm_name)
    xen.vm_start(vm_name)

    # --- Wait for VM to startup

    prober = PortProber(vm_host)
    
    print("Waiting for VM to become available...")
    while not prober.is_port_open(3389):
        pass

    log.info("VM is available at %s:3389" % vm_host)

    print("Stopping VM...")
    xen.vm_shutdown(vm_name)
    print("Revert to snapshot...")
    xen.vm_snapshot_revert(vm_name, "ss-"+vm_name)
