#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2021 LUNARC, Lund University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
LHPC VM management module

Contains classes for managing running VM resources.
"""

import os, json
import sys, subprocess, pickle, socket, time
import logging as log
import configparser
import datetime

from filelock import Timeout, FileLock

class SlurmVMConfig(object):
    """SLURMVM Configuration class

    Reads and manages the slurmvm configuration settings
    """
    def __init__(self):

        self.__default_config_file = "/etc/slurm/lhpcvm.conf"
        self.__fallback_config_file = "./lhpcvm.conf"
        self.__used_config_file = ""
        self.xen_server_hostname = "localhost"
        self.log_level="DEBUG"
        self.snapshot_prefix="ss"
        self.use_snapshot = False
        self.manage_vm = False
        self.manage_server = True
        self.vm_dict = {}

        self.win10_logoff_script = ""
        self.win10_update_script = ""
        self.win10_reboot_script = ""

        self.config_valid = False

        self.reboot_server_days = []
        self.reboot_server = False

        self.__read_config()

    def __read_config(self):
        """Read configuration file"""

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
            #try:
            self.config = configparser.ConfigParser()
            print("Reading", self.__used_config_file)
            self.config.read(self.__used_config_file)
            self.config_valid = True
            #except:
            #print("Couldn't parse configuration file at /etc/slurm/lhpcvm.conf")
            #self.config_valid = False
            #return
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

        if "manage_vm" in default_params:
            value = self.config.get("DEFAULT", "manage_vm")
            if value == "yes":
                self.manage_vm = True
            else:
                self.manage_vm = False

        if "manage_server" in default_params:
            value = self.config.get("DEFAULT", "manage_server")
            if value == "yes":
                self.manage_server = True
            else:
                self.manage_server = False

        if "reboot_server_days" in default_params:
            value = self.config.get("DEFAULT", "reboot_server_days")

            days_list = []

            if value != "":
                days = value.split(",")

            for day in days:
                if day.strip() in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    days_list.append(day.strip())

            self.reboot_server_days = days_list

        if "reboot_server" in default_params:
            value = self.config.get("DEFAULT", "reboot_server")
            if value == "yes":
                self.reboot_server = True
            else:
                self.reboot_server = False

        self.vm_dict = {}
        self.vm_actions = {}
        self.vm_enabled = {}

        for vm in self.config.sections():
            options = self.config.options(vm)

            if "-default" in vm:
                kind = vm.split("-")[0]
                self.vm_actions[kind] = {}
                if "logoff_users_script" in options:
                    self.vm_actions[kind]["logoff_users_script"] = self.config.get(vm, "logoff_users_script")
                if "disable_user_script" in options:
                    self.vm_actions[kind]["disable_user_script"] = self.config.get(vm, "disable_user_script")
                if "enable_user_script" in options:
                    self.vm_actions[kind]["enable_user_script"] = self.config.get(vm, "enable_user_script")
                if "check_reboot_script" in options:
                    self.vm_actions[kind]["check_reboot_script"] = self.config.get(vm, "check_reboot_script")
                if "reboot_script" in options:
                    self.vm_actions[kind]["reboot_script"] = self.config.get(vm, "reboot_script")
                if "update_script" in options:
                    self.vm_actions[kind]["update_script"] = self.config.get(vm, "update_script")
                if "system_account" in options:
                    self.vm_actions[kind]["system_account"] = self.config.get(vm, "system_account")
            else:
                vm_name = ""
                vm_hostname = ""
                vm_kind = ""

                if "name" in options:
                    vm_name = self.config.get(vm, "name")

                if "hostname" in options:
                    vm_hostname = self.config.get(vm, "hostname")

                if "kind" in options:
                    vm_kind = self.config.get(vm, "kind")

                if "enabled" in options:
                    if self.config.get(vm, "enabled") == "no":
                        self.vm_enabled[vm_name] = False
                    else:
                        self.vm_enabled[vm_name] = True
                else:
                    self.vm_enabled[vm_name] = True

                if vm_name!="" and vm_hostname!="":
                    self.vm_dict[vm_name] = {}
                    self.vm_dict[vm_name]["hostname"] = vm_hostname
                    self.vm_dict[vm_name]["kind"] = vm_kind

        self.config_valid = True

    def show_config(self):
        """Show configuration"""

        print("-----------------------------------")
        print("SLURM Session manager configuration")
        print("-----------------------------------")
        print()
        print("Log level       :", self.log_level)
        print("Reboot server   :", self.reboot_server)
        print("Reboot days     :", self.reboot_server_days)
        print()
        print("Default actions:")
        print()

        for kind in self.vm_actions.keys():
            print("Default actions for %s:" % kind)
            for prop in self.vm_actions[kind].keys():
                print("\t%s = %s" % (prop, self.vm_actions[kind][prop]))

        print()
        print("Configured VM:s:")
        print()
        for vm in self.vm_dict.keys():
            print("VM:", vm, "ip =", self.vm_dict[vm]["hostname"])
            for prop in self.vm_dict[vm].keys():
                print("\t%s = %s" % (prop, self.vm_dict[vm][prop]))
            if self.vm_enabled[vm]:
                print("\tenabled = yes")
            else:
                print("\tenabled = no")
            print()



        if self.config_valid:
            print("Configuration is valid.")
        else:
            print("Configuration is not valid.")

    def vm_kind(self, name):
        if name in self.vm_dict:
            return self.vm_dict[name]["kind"]
        else:
            return ""

    def vm_logoff_users_script(self, kind):
        if kind in self.vm_actions:
            if 'logoff_users_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['logoff_users_script']

        return ""

    def vm_enable_user_script(self, kind):
        if kind in self.vm_actions:
            if 'enable_user_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['enable_user_script']

        return ""

    def vm_disable_user_script(self, kind):
        if kind in self.vm_actions:
            if 'disable_user_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['disable_user_script']

        return ""

    def vm_update_script(self, kind):
        if kind in self.vm_actions:
            if 'update_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['update_script']

        return ""

    def vm_check_reboot_script(self, kind):
        if kind in self.vm_actions:
            if 'check_reboot_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['check_reboot_script']

        return ""

    def vm_reboot_script(self, kind):
        if kind in self.vm_actions:
            if 'reboot_script' in self.vm_actions[kind]:
                return self.vm_actions[kind]['reboot_script']

        return ""

    def vm_system_account(self, kind):
        if kind in self.vm_actions:
            if 'system_account' in self.vm_actions[kind]:
                return self.vm_actions[kind]['system_account']

        return ""



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

        # Add last_reboot attribute to list if it does
        # not exist.

        log.debug("Idle VMs:")
    
        for idle_vm in self.idle_list:
            if len(idle_vm)<3:
                idle_vm.append(datetime.datetime.now())

        for running_job in self.running_dict.keys():
            if len(self.running_dict[running_job])<3:
                self.running_dict[running_job].append(datetime.datetime.now())   
            

    def save(self):
        """Save current database to disk"""

        log.debug("VMTracker.save()")

        with self.lock:
            with open(self.state_filename, "wb+") as f:
                tmp_dict = self.__dict__.copy()
                del tmp_dict["lock"]
                pickle.dump(tmp_dict, f)

    def add_vm(self, name, hostname, last_reboot=""):
        """Add a vm to list of resources."""

        log.debug("VMTracker.add_vm(%s, %s)" % (name, hostname))
        if last_reboot == "":
            self.idle_list.append([name, hostname, datetime.datetime.now()])
        else:
            self.idle_list.append([name, hostname, last_reboot])

    def init_tracker(self):
        """Initialise initial resources."""

        log.debug("VMTracker.init_tracker()")

        vm_dict = self.slurm_vm_config.vm_dict

        for vm in vm_dict.keys():
            log.debug("Adding VM " + vm + "(" + vm_dict[vm]["hostname"] + ") to initial configuration.")
            self.add_vm(vm, vm_dict[vm]["hostname"])

    def aquire_vm(self, job_id):
        """Aquire a vm for a specific job_id"""

        log.debug("VMTracker.aquire_vm(%s)" % job_id)

        vm_enabled = self.slurm_vm_config.vm_enabled

        if len(self.idle_list)>0:
            for i, idle_vm in enumerate(self.idle_list):
                vm_name = idle_vm[0]
                if vm_enabled[vm_name]:
                    self.idle_list.pop(i)
                    self.running_dict[job_id] = [idle_vm[0], idle_vm[1], idle_vm[2]]       
                    self.save()
                    return idle_vm[0], idle_vm[1]

            return "", ""       

            # vm_info = self.idle_list.pop()
            # self.running_dict[job_id] = [vm_info[0], vm_info[1], vm_info[2]]
            # self.save()
            # return vm_info[0], vm_info[1]
        else:
            return "", ""

    def release_vm(self, job_id):
        """Release a vm from a job_id"""

        log.debug("VMTracker.release_vm(%s)" % job_id)

        if job_id in self.running_dict:
            vm_info = self.running_dict.pop(job_id)
            self.add_vm(vm_info[0], vm_info[1], vm_info[2])
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

    def host_info(self, host):
        """Return host information"""

        host_info = ["", "", datetime.datetime.today()]

        for vm in self.idle_list:
            if vm[1] == host:
                return [vm[0], vm[1], vm[2]]
        
        for job_id in self.running_dict.keys():
            if self.running_dict[job_id][1] == host:
                return self.running_dict[job_id][:]

        return host_info

    def need_reboot(self, host, days):
        """Check if reboot is needed."""

        current_date = datetime.datetime.today()
        current_day = current_date.strftime('%A')

        if current_day in days:
            log.info("Checking if reboot of %s is scheduled." % host)
            host_info = self.host_info(host)
            reboot_date = host_info[2]

            diff = current_date - reboot_date

            log.debug("%s was rebooted at: %s" % (host, reboot_date))

            if diff.days != 0:
                log.info("Reboot of %s required." % host)
                return True
            else:
                log.info("No reboot of %s required." % host)
                return False

        else:
            log.debug("Reboot checking performed.")
            return False

    def update_reboot_status(self, host):
        """Update time stamp for last reboot"""

        for vm in self.idle_list:
            if vm[1] == host:
                vm[2] = datetime.datetime.today()
        
        for job_id in self.running_dict.keys():
            if self.running_dict[job_id][1] == host:
                self.running_dict[job_id][2] = datetime.datetime.today()        


class VM:
    no_error = 0
    script_exec_failure = 1    

    def __init__(self, hostname, user=""):
        self.__hostname = hostname
        self.__user = user

        self.__logoff_users_script = ""
        self.__update_script = ""
        self.__disable_user_script = ""
        self.__enable_user_script = ""
        self.__check_reboot_script = ""
        self.__reboot_script = ""

        self.__error_status = VM.no_error

    def clear_error_status(self):
        self.__error_status = VM.no_error

    def in_error(self):
        return self.__error_status!=VM.no_error

    def logoff_users(self):
        """Log off all users on server"""
        pass

    def disable_user(self):
        """Disable user account"""
        pass

    def enable_user(self):
        """Enable user account"""
        pass

    def reboot(self):
        pass

    def update(self):
        """Update server"""
        pass

    @property
    def logoff_users_script(self):
        return self.__logoff_users_script

    @logoff_users_script.setter
    def logoff_users_script(self, value):
        self.__logoff_users_script = value

    @property
    def update_script(self):
        return self.__update_script

    @update_script.setter
    def update_script(self, value):
        self.__update_script = value

    @property
    def disable_user_script(self):
        return self.__disable_user_script

    @disable_user_script.setter
    def disable_user_script(self, value):
        self.__disable_user_script = value

    @property
    def enable_user_script(self):
        return self.__enable_user_script

    @enable_user_script.setter
    def enable_user_script(self, value):
        self.__enable_user_script = value

    @property
    def check_reboot_script(self):
        return self.__check_reboot_script

    @check_reboot_script.setter
    def check_reboot_script(self, value):
        self.__check_reboot_script = value

    @property
    def reboot_script(self):
        return self.__reboot_script

    @reboot_script.setter
    def reboot_script(self, value):
        self.__reboot_script = value

    @property
    def hostname(self):
        return self.__hostname
    
    @property
    def user(self):
        return self.__user

    @property 
    def error_status(self):
        return self.__error_status
    
    @error_status.setter
    def error_status(self, status):
        self.__error_status = status


class Win10VM(VM):
    def __init__(self, hostname, user=""):
        super().__init__(hostname, user)

    def __exec_cmd(self, cmd):
        """Execute a command and return output"""

        self.clear_error_status()

        try:
            output = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            log.error("Process: %s returned exit status of %d" % (cmd, e.returncode))
            self.error_status = VM.script_exec_failure
            return ""
            
        return output.decode('ascii')

    def ssh_cmd(self, cmd):
        """Execute a command on the VM"""
        log.debug("%s" % cmd)

        return self.__exec_cmd("ssh %s@%s '%s'" % (self.user, self.hostname, cmd))

    def ssh_pipe_script(self, script):
        """Execute a command on the VM"""
        log.debug("%s" % script)

        if self.user == "":
            return self.__exec_cmd("ssh %s < %s" % (self.hostname, script))
        else:
            return self.__exec_cmd("ssh %s@%s < %s" % (self.user, self.hostname, script))

    def logoff_users(self):
        """Log off all users on server"""
        if self.logoff_users_script != "":
            self.__exec_cmd(self.logoff_users_script + " " + self.hostname)

    def update(self):
        """Update server"""
        if self.update_script != "":
            self.__exec_cmd(self.update_script + " " + self.hostname)

    def disable_user(self, username):
        if self.disable_user_script!="":
            self.__exec_cmd(self.disable_user_script + " " + username)

    def enable_user(self, username):
        if self.enable_user_script!="":
            self.__exec_cmd(self.enable_user_script + " " + username)

    def check_reboot(self):
        if self.check_reboot_script!="":
            self.__exec_cmd(self.check_reboot_script + " " + self.hostname)

    def reboot(self):
        if self.reboot_script!="":
            self.__exec_cmd(self.reboot_script + " " + self.hostname)

class CentOS7VM(VM):
    def __init__(self, hostname):
        super().__init__(hostname)

    def logoff_users(self):
        """Log off all users on server"""
        pass 

    def update(self):
        """Update server"""
        pass

if __name__ == "__main__":

    # --- Configure logging - All messages from prolog/epilog uses Python logging.

    root = log.getLogger()
    root.setLevel(log.DEBUG)

    handler = log.StreamHandler(sys.stdout)
    handler.setLevel(log.DEBUG)
    formatter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    slurm_vm_config = SlurmVMConfig()

    if slurm_vm_config.config_valid:
        slurm_vm_config.show_config()
    else:
        print("No valid config file.")

    vm_tracker = VMTracker(slurm_vm_config)
    vm_tracker.status()
    vm_tracker.save()

    host = "10.18.50.23"

    #if vm_tracker.need_reboot(host, slurm_vm_config.reboot_server_days):
    #    vm_tracker.update_reboot_status(host)

    for i in range(20):
        vm_name, vm_host = vm_tracker.aquire_vm(str(i))
        print(vm_name, vm_host)

    for i in range(20):
        vm_name, vm_host = vm_tracker.release_vm(str(i))
        print(vm_name, vm_host)


    #vm_tracker.status()
    #vm_tracker.save()

    sys.exit(0)

