#!/usr/bin/python
"""
LHPC VM management module

Contains classes for managing running VM resources
"""

import os, pwd, fcntl, json
import sys, subprocess, pickle, socket, time
import logging as log
import ConfigParser as configparser


from filelock import Timeout, FileLock

class SlurmVMConfig(object):
    def __init__(self):

        self.xen_server_hostname = "localhost"
        self.log_level="DEBUG"
        self.snapshot_prefix="ss"
        self.vm_dict = {}

        self.config_valid = False

        self.__read_config()

    def __read_config(self):

        self.config_valid = False

        try:
            self.config = configparser.ConfigParser()
            self.config.read("/etc/slurm/lhpcvm.conf")
        except:
            print("Couldn't parse configuration file at /etc/slurm/lhpcvm.conf")
            return

        default_params = self.config.defaults()

        if "xenserverhost" in default_params:
            self.xen_server_hostname = self.config.get("DEFAULT", "xenserverhost")

        if "loglevel" in default_params:
            self.log_level = self.config.get("DEFAULT", "loglevel")

        if "snapshotprefix" in default_params:
            self.snapshot_prefix = self.config.get("DEFAULT", "snapshotprefix")

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
        print(self.xen_server_hostname)
        print(self.log_level)
        print(self.snapshot_prefix)

        for vm in self.vm_dict.keys():
            print(vm, self.vm_dict[vm])

        print(self.config_valid)


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

        server_ip = socket.gethostbyname(self.hostname)

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
            log.error("Connection timeout.")
            return False

        except KeyboardInterrupt:
            log.error("You pressed Ctrl+C")
            return False

        except socket.gaierror:
            log.error('Hostname could not be resolved. Exiting')
            return False

        except socket.error:
            log.error("Couldn't connect to server")
            return False

class XenServer(object):
    """Class for controlling a XenServer Hypervisor"""
    def __init__(self, hostname, dryrun=False):
        self.hostname = hostname
        self.dryrun = dryrun

    def exec_cmd(self, cmd):
        """Execute a command and return output"""
        output = subprocess.check_output(cmd, shell=True)
        return output

    def xe(self, cmd):
        """Execute a xe command on the XenServer"""
        log.debug("Executing: "+cmd)
        return self.exec_cmd("ssh %s 'xe %s'" % (self.hostname, cmd))
    
    def vm_list(self):
        """Return a dict of vm:s"""

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

        vm_dict = self.vm_list()

        if vm_name in vm_dict:
            return vm_dict[vm_name]["state"] == "running"
        else:
            return False

    def vm_start(self, vm_name):
        """Start a named vm"""
        output = self.xe("vm-start vm=%s" % vm_name)
        log.debug(output)

    def vm_shutdown(self, vm_name):
        """Shutdown a named vm"""
        output = self.xe("vm-shutdown vm=%s" % vm_name)
        log.debug(output)

    def vm_snapshot(self, vm_name, snapshot_name):
        """Take a snapshot of named vm"""

        output = self.xe('vm-snapshot new-name-label=%s vm=%s' % (snapshot_name, vm_name))

    def vm_snapshot_revert(self, vm_name, snapshot_name):
        """Revert to a named snapshot"""

        snapshots = self.snapshot_list()

        ss_uuid = snapshots[snapshot_name]["uuid"]

        self.xe("snapshot-revert snapshot-uuid=%s" % (ss_uuid))

    def snapshot_list(self):
        """Return a dict of snapshots"""
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


class VMTracker(Singleton, object):
    """Class for tracking running vm:s"""

    def __init__(self, slurm_vm_config):
        Singleton.__init__(self)

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

        with self.lock:
            with open(self.state_filename, "wb+") as f:
                tmp_dict = self.__dict__.copy()
                del tmp_dict["lock"]
                pickle.dump(tmp_dict, f)

    def add_vm(self, hostname):
        """Add a vm to list of resources."""

        self.idle_list.append(hostname)

    def init_tracker(self):
        """Initialise initial resources."""

        vm_dict = self.slurm_vm_config.vm_dict

        for vm in vm_dict.keys():
            log.debug("Adding VM "+vm_dict[vm]+" to initial configuration.")
            self.add_vm(vm_dict[vm])

    def aquire_vm(self, job_id):
        """Aquire a vm for a specific job_id"""

        if len(self.idle_list)>0:
            vm_host = self.idle_list.pop()
            self.running_dict[job_id] = vm_host
            self.save()
            return vm_host
        else:
            return ""

    def release_vm(self, job_id):
        """Release a vm from a job_id"""

        if job_id in self.running_dict:
            vm_host = self.running_dict.pop(job_id)
            self.add_vm(vm_host)
            self.save()
            return vm_host
        else:
            return ""

    def has_user_store(self):
        """Return state of user store directory"""

        self.store_dir = os.path.join(self.home_dir, ".lhpc")
        return os.path.exists(self.store_dir)

    def setup_user_store(self):
        """Setup user store directory with correct permissions"""

        if not self.has_user_store():
            log.debug("Creating user store directory.")
            os.mkdir(self.store_dir)
            os.chown(self.store_dir, self.user_id, self.group_id)
            os.chmod(self.store_dir, 0o700)

    def user_store_dir(self):
        """Return user store directory"""

        if not self.has_user_store():
            self.setup_user_store()
        return self.store_dir

    def write_job_hostfile(self, job_id, vm_host):
        """Write job host file containing ip of running VM"""

        store_dir = self.user_store_dir()
        job_host_filename = os.path.join(store_dir, "vm_host_%s.ip" % job_id.strip())

        log.debug("Creating job ip-file: "+job_host_filename)

        with open(job_host_filename, "w") as f:
            f.write(vm_host+"\n")

        os.chown(job_host_filename, self.user_id, self.group_id)
        os.chmod(job_host_filename, 0o700)

    def remove_job_hostfile(self, job_id, vm_host):
        """Remove a job host file when not needed anymore"""

        store_dir = self.user_store_dir()
        job_host_filename = os.path.join(store_dir, "vm_host_%s.ip" % job_id.strip())

        log.debug("Removing job ip-file: "+job_host_filename)

        if os.path.exists(job_host_filename):
            os.remove(job_host_filename)

    def status(self):
        """Print status of data base"""

        log.debug("Idle VMs:")
    
        for idle_vm in self.idle_list:
            log.debug(idle_vm)
    
        log.debug("Jobs with running VMs:")

        for job_id in self.running_dict.keys():
            log.debug(job_id, self.running_dict[job_id])


if __name__ == "__main__":

    slurm_vm_config = SlurmVMConfig()
    slurm_vm_config.show_config()

    #xen = XenServer('rviz-lab-xen.lunarc.lu.se')

    #xen.vm_stop("win10m-1")
    #xen.vm_snapshot("win10m-1", "ss-win10m-1")

    #xen.vm_start("win10m-1")

    #if xen.is_vm_running("win10m-1"):
    #    print("VM is running.")
    #else:
    #    print("VM is not running.")

    #xen.vm_snapshot_revert("win10m-1", "ss-win10m-1")
    #xen.vm_start("win10m-1")

    #prober = PortProber("win10m-1.lunarc.lu.se")
    
    #print("Waiting for VM to become available...")
    #while not prober.is_port_open(3389):
    #    pass

    #print("VM is available at 3389")
