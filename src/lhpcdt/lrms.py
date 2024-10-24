#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2023 LUNARC, Lund University
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

"""Base classes for interacting with resource management systems."""

import os
import subprocess
import time
import datetime
import getpass
import sys
import shutil

from subprocess import Popen, PIPE, STDOUT

from lhpcdt import hostlist
from lhpcdt import config
from lhpcdt import jobs


def execute_cmd(cmd):
    """Wrapper function for calling an external process"""
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = p.stdout.read()
    retval = p.wait()
    return output


class GrantFile:
    """Class for accessing LUNARC grantfiles"""

    def __init__(self, filename):
        """Class constructor"""
        self.filename = filename
        self.verbose = True

        self._parse_grantfile()

    def _parse_grantfile(self):
        """Parse grantfile"""

        f = open(self.filename, "r")
        lines = f.readlines()
        f.close()

        self.projects = {}

        for line in lines:
            if line[0] != '#':
                items = line.split(",")
                if len(items) == 6:
                    name = items[0]
                    self.projects[name] = {}
                    self.projects[name]["start_date"] = items[1]
                    self.projects[name]["end_date"] = items[2]
                    self.projects[name]["core_hours"] = int(items[3])
                    self.projects[name]["partition"] = items[4]
                    self.projects[name]["pi"] = items[5].split("#")[0]
                    self.projects[name]["users"] = items[5].split("#")[
                        1].split()

    def query_active_projects(self, user):
        """Query for an active project for user"""

        active_projects = []

        for project in list(self.projects.keys()):
            if user in self.projects[project]["users"]:
                if self.verbose:
                    print("Found user %s in project %s in grantfile %s" %
                          (user, project, self.filename))
                start_date = datetime.datetime.strptime(
                    self.projects[project]["start_date"], "%Y%m%d")
                end_date = datetime.datetime.strptime(
                    self.projects[project]["end_date"], "%Y%m%d")

                current_date = datetime.datetime.today()

                if self.verbose:
                    print("Project lifetime: %s-%s" % (start_date, end_date))

                if (start_date < current_date) and (current_date < end_date):
                    if self.verbose:
                        print("Project is ACTIVE")
                    active_projects.append(project)
                else:
                    if self.verbose:
                        print("Project is EXPIRED")

        return active_projects


class Queue(object):
    """Class for encapsuling a SLURM queue"""

    def __init__(self):
        """
        JOBID PARTITION		NAME	 USER	 STATE		 TIME TIMELIMIT	 NODES NODELIST(REASON)
        2981700		brand 5cpu.scr	 kurs16	 RUNNING 2-02:39:48 6-00:00:00		1 an225
        """
        self.squeueParams = ["jobid", "partition", "name", "user",
                             "state", "time", "timelimit", "nodes", "nodelist", "timeleft",
                             "deps", "account", "cpus", "features", "timestart"]

        # jobinfo squeue format  - %.7i %.9P %.25j %.8u %14a %.2t %.19S %.10L %.8Q %.4C %.16R %.12f %E
        #                             x    x     x    x         x     x                     x
        self.squeueFormat = "%.7i;%.9P;%.20j;%.12u;%.8T;%.10M;%.9l;%.6D;%R;%L;%E;%14a;%4C;%.12f;%S"
        self.jobList = []
        self.jobs = {}
        self.userJobs = {}
        self.running_jobs = {}
        self.pending_jobs = {}
        self.max_nodes = -1
        self.max_cpus = -1

    def job_info(self, jobid):
        """Return information on job jobid"""
        return execute_cmd('scontrol show job %s' % jobid)

    def update(self):
        """Update queue information"""
        output = execute_cmd(
            'squeue --noheader --format="%s"' % self.squeueFormat)
        lines = output.split("\n")

        self.max_nodes = -1
        self.max_cpus = -1

        self.jobs = {}
        self.jobList = []
        self.userJobs = {}

        for line in lines:
            parts = line.split(";")
            if len(parts) > 2:
                id = parts[0].strip()
                if not (id in self.jobs):
                    self.jobs[id] = {}
                    job = {"jobid": id}
                for i in range(1, 15):
                    self.jobs[id][self.squeueParams[i]] = parts[i].strip()
                    job[self.squeueParams[i]] = parts[i].strip()

                if job["state"] == "RUNNING":
                    self.running_jobs[id] = job

                if job["state"] == "PENDING":
                    self.pending_jobs[id] = job

                if int(job["nodes"]) > self.max_nodes:
                    self.max_nodes = int(job["nodes"])

                if int(job["cpus"]) > self.max_cpus:
                    self.max_cpus = int(job["cpus"])

                self.jobList.append(job)

                # if not self.userJobs.has_key(self.jobs[id]["user"]):

                if not (self.jobs[id]["user"] in self.userJobs):
                    self.userJobs[self.jobs[id]["user"]] = {}

                self.userJobs[self.jobs[id]["user"]][id] = self.jobs[id]


class Slurm(object):
    """SLURM Interface class"""

    def __init__(self):
        """Slurm constructor"""
        self.partitions = []
        self.node_lists = {}
        self.verbose = True
        self.job_output_dir = os.path.join(os.path.expanduser("~"), ".lhpc")

    def is_exec_available(self, executable):
        """Check if executable is available"""
        exec_found = shutil.which(executable)
        #if self.verbose:
        #    print("Executable %s is %s" % (executable, "found" if exec_found else "not found"))
        return shutil.which(executable) is not None

    def check_environment(self):
        """Check if SLURM commands are available"""

        self.sbatch_available = self.is_exec_available("sbatch")
        self.squeue_available = self.is_exec_available("squeue")
        self.scancel_available = self.is_exec_available("scancel")
        self.sinfo_available = self.is_exec_available("sinfo")

        return self.sbatch_available and self.squeue_available and self.scancel_available and self.sinfo_available


    def __include_part(self, part, exclude_set):
        include = True

        if len(exclude_set)>0:
            for exclude_pattern in exclude_set:
                if exclude_pattern in part:
                    include = False

        return include

    def query_partitions(self, exclude_set={}):
        """Query partitions in slurm."""
        p = Popen("sinfo", stdout=PIPE, stderr=PIPE,
                  shell=True, universal_newlines=True)
        squeue_output = p.communicate()[0].split("\n")

        self.partitions = []
        self.node_lists = {}

        part_lines = squeue_output[1:]

        for line in part_lines:
            if line != "":
                part_name = line.split()[0].strip()
                node_list = line.split()[5]
                if part_name.find("*") != -1:
                    part_name = part_name[:-1]
                if self.__include_part(part_name, exclude_set):
                    self.partitions.append(part_name)
                    if part_name in self.node_lists:
                        self.node_lists[part_name] = self.node_lists[part_name] + \
                            hostlist.expand_hostlist(node_list)
                    else:
                        self.node_lists[part_name] = hostlist.expand_hostlist(
                            node_list)

        self.partitions = list(set(self.partitions))


    """
    NodeName=eg24 Arch=x86_64 CoresPerSocket=8
       CPUAlloc=0 CPUErr=0 CPUTot=16 CPULoad=0.01
       AvailableFeatures=rack-f1,kepler,mem96GB,gpu8k20
       ActiveFeatures=rack-f1,kepler,mem96GB,gpu8k20
       Gres=gpu:k20:6
       NodeAddr=eg24 NodeHostName=eg24 Version=17.02
       OS=Linux RealMemory=94000 AllocMem=0 FreeMem=94163 Sockets=2 Boards=1
       State=IDLE ThreadsPerCore=1 TmpDisk=0 Weight=1 Owner=N/A MCS_label=N/A
       Partitions=lvis 
       BootTime=2018-02-05T18:02:37 SlurmdStartTime=2018-02-05T18:05:18
       CfgTRES=cpu=16,mem=94000M
       AllocTRES=
       CapWatts=n/a
       CurrentWatts=0 LowestJoules=0 ConsumedJoules=0
       ExtSensorsJoules=n/s ExtSensorsWatts=0 ExtSensorsTemp=n/s
    """

    def query_node(self, node):
        """Query information on node"""
        p = Popen("scontrol show node %s" % node, stdout=PIPE,
                  stderr=PIPE, shell=True, universal_newlines=True)
        scontrol_output = p.communicate()[0].split("\n")

        node_dict = {}

        for line in scontrol_output:
            var_pairs = line.strip().split(" ")
            if len(var_pairs) >= 1:
                for var_pair in var_pairs:
                    if len(var_pair) > 0:
                        if var_pair.find("=") != -1:
                            var_name = var_pair.split("=")[0]
                            var_value = var_pair.split("=")[1]
                            node_dict[var_name] = var_value

        return node_dict

    def query_nodes(self):
        """Query information on node"""
        p = Popen("scontrol show nodes -o", stdout=PIPE,
                  stderr=PIPE, shell=True, universal_newlines=True)
        scontrol_output = p.communicate()[0].split("\n")

        node_dict = {}

        current_node_name = ""

        for line in scontrol_output:
            var_pairs = line.strip().split(" ")
            if len(var_pairs) >= 1:
                for var_pair in var_pairs:
                    if len(var_pair) > 0:
                        if var_pair.find("=") != -1:
                            var_name = var_pair.split("=")[0]
                            var_value = var_pair.split("=")[1]

                            if var_name == "NodeName":
                                current_node_name = var_value
                                node_dict[var_value] = {}
                            else:
                                node_dict[current_node_name][var_name] = var_value

        return node_dict
    
    def query_reservations(self):
        """Query SLURM reservations"""

        """
        ReservationName=lu2023-2-82 StartTime=2023-10-16T14:38:40 EndTime=2040-01-01T00:00:00 Duration=5920-10:21:20
        Nodes=cx[02-03] NodeCnt=2 CoreCnt=96 Features=(null) PartitionName=(null) Flags=IGNORE_JOBS,SPEC_NODES
        TRES=cpu=96
        Users=(null) Groups=(null) Accounts=lu2023-2-82 Licenses=(null) State=ACTIVE BurstBuffer=(null) Watts=n/a
        MaxStartDelay=(null)

        ReservationName=lu2023-2-18 StartTime=2023-11-02T14:26:25 EndTime=2040-01-01T00:00:00 Duration=5903-09:33:35
        Nodes=ca[01-18] NodeCnt=18 CoreCnt=360 Features=(null) PartitionName=(null) Flags=IGNORE_JOBS,SPEC_NODES
        TRES=cpu=360
        Users=(null) Groups=(null) Accounts=lu2023-2-18 Licenses=(null) State=ACTIVE BurstBuffer=(null) Watts=n/a
        MaxStartDelay=(null)

        ReservationName=reimann StartTime=2024-03-21T08:57:04 EndTime=2040-01-01T00:00:00 Duration=5763-15:02:56
        Nodes=ca[19-22] NodeCnt=4 CoreCnt=96 Features=(null) PartitionName=(null) Flags=IGNORE_JOBS,SPEC_NODES
        TRES=cpu=96
        Users=(null) Groups=(null) Accounts=lu2024-2-46 Licenses=(null) State=ACTIVE BurstBuffer=(null) Watts=n/a
        MaxStartDelay=(null)

        ReservationName=RPJM-course StartTime=2024-10-24T09:00:00 EndTime=2024-10-24T16:00:00 Duration=07:00:00
        Nodes=cn[157-158] NodeCnt=2 CoreCnt=96 Features=(null) PartitionName=(null) Flags=IGNORE_JOBS,DAILY,SPEC_NODES
        TRES=cpu=96
        Users=(null) Groups=(null) Accounts=lu2024-7-80 Licenses=(null) State=INACTIVE BurstBuffer=(null) Watts=n/a
        MaxStartDelay=(null)        
        """

        p = Popen("scontrol show res", stdout=PIPE,
                  stderr=PIPE, shell=True, universal_newlines=True)
        scontrol_output = p.communicate()[0].split("\n")

        reservations = []

        for line in scontrol_output:
            if line.find("ReservationName") != -1:
                reservation = {}
                parts = line.split(" ")
                for part in parts:
                    if part.find("=") != -1:
                        key = part.split("=")[0]
                        value = part.split("=")[1]
                        reservation[key] = value

            elif line.find("Nodes") != -1:
                parts = line.split(" ")
                for part in parts:
                    if part.find("=") != -1:
                        key = part.split("=")[0]
                        value = part.split("=")[1]
                        reservation[key] = value

            elif line.find("Users") != -1:
                parts = line.split(" ")
                for part in parts:
                    if part.find("=") != -1:
                        key = part.split("=")[0]
                        value = part.split("=")[1]
                        reservation[key] = value

                reservations.append(reservation)

        return reservations

    def __include_feature(self, feature, exclude_set):
        include = True
        for exclude_pattern in exclude_set:
            if exclude_pattern in feature:
                include = False

        return include

    def query_features(self, part, exclude_set={}):
        """Query features of partition"""

        if self.verbose:
            print(f"Querying {part} for features ...")

        node_info = self.query_nodes()

        feature_list = []

        for node in list(node_info.keys()):
            if "Partitions" in node_info[node]:
                if node_info[node]["Partitions"] == part:
                    features = node_info[node]["ActiveFeatures"].split(",")
                    for feature in features:
                        if self.__include_feature(feature, exclude_set):
                            feature_list.append(feature)

        return list(set(feature_list))

    def query_gres(self, part):
        """Query features of partition"""

        node_list = self.node_lists[part]

        gres_list = []

        for node in node_list:
            node_info = self.query_node(node)

            gres = node_info["Gres"].split(",")
            gres_list.extend(gres)

        return list(set(gres_list))

    def submit(self, job):
        """Submit job to SLURM"""

        # Write job script to file (Debugging)

        cfg = config.GfxConfig.create()

        home_dir = os.getenv("HOME")

        if cfg.debug_mode:
            debug_script_filename = os.path.join(home_dir, "gfxjob.sh")

            submit_script = open(debug_script_filename, "w")
            submit_script.write(job.script)
            submit_script.close()

        # Submit from user home dir.

        os.chdir(home_dir)

        # Start a sbatch process for job submission

        p = Popen("sbatch", stdout=PIPE, stdin=PIPE, stderr=PIPE,
                  shell=True, universal_newlines=True)
        sbatch_output = p.communicate(input=job.script)[0].strip()

        if sbatch_output.find("Submitted batch") != -1:
            job.id = int(sbatch_output.split()[3])
            return True
        else:
            job.id = -1
            return False

    def job_status(self, job):
        """Query status of job"""
        p = Popen("squeue -j " + str(job.id) + " -t PD,R -h -o '%t;%N;%L;%M;%l'",
                  stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
        squeue_output = p.communicate()[0].strip().split(";")

        #print(squeue_output)

        if len(squeue_output) > 1:
            job.status = squeue_output[0]
            job.nodes = squeue_output[1]
            job.timeLeft = squeue_output[2]
            job.timeRunning = squeue_output[3]
            job.timeLimit = squeue_output[4]
        else:
            job.status = ""
            job.nodes = ""
            job.timeLeft = ""
            job.timeRunning = ""
            job.timeLimit = ""

    def cancel_job_with_id(self, jobid):
        """Cancel job"""
        result = subprocess.call("scancel %d" % (jobid), shell=True)
        return result

    def cancel_job(self, job):
        """Cancel job"""
        try:
            result = subprocess.call("scancel %d" % (job.id), shell=True)
            job.id = -1
            job.status = ""
        except:
            return -1

        return result

    def job_output(self, job):
        """Query job output"""
        if self.is_running(job):
            #output_filename = os.path.join(
            #    os.environ["HOME"], "slurm-%d.out" % job.id)

            output_filename = os.path.join(self.job_output_dir, "lhpcdt-%d.out" % job.id)
            
            if os.path.exists(output_filename):
                output_file = open(output_filename, "r")
                output = output_file.readlines()
                output_file.close()
                return output
            else:
                print("Couldn't find: "+output_filename)
                return []
        else:
            return []

    def wait_for_start(self, job):
        """Wait for job to start"""
        self.job_status(job)

        while job.status != "R":
            self.job_status(job)
            time.sleep(1)

    def is_running(self, job):
        self.job_status(job)
        return job.status == "R"

    def has_started(self, job):
        """Query if job has started"""
        self.job_status(job)
        return job.status == "R"

    def is_waiting(self, job):
        """Query if job is in an non-running state"""
        self.job_status(job)
        return job.status != "R"
    
class Accounting:
    """
    sacct -o jobid%20,jobname%50,state%30,exitcode%20
    """

    def __init__(self):
        self.job_status = {}
        self.query_job_accouting()

    def query_job_accouting(self):
        output = execute_cmd("sacct -p -n -b")
        lines = output.split("\n")

        for line in lines:
            items = line.split("|")
            job = items[0].split(".")

            if len(items)<=1:
                continue

            if len(job)>1:
                job_id = job[0]
                job_step = job[1]
            else:
                job_id = job[0]
                job_step = "first"

            job_state = items[1]
            job_exit_code = items[2]

            if not job_id in self.job_status:
                self.job_status[job_id] = {}
                self.job_status[job_id][job_step] = []

            if not job_step in self.job_status[job_id]:
                self.job_status[job_id][job_step] = []

            self.job_status[job_id][job_step].append(job_state)
            self.job_status[job_id][job_step].append(job_exit_code)

class AccountManager:
    def __init__(self, user=""):
        self.user = user
        self.user_account_dict = {}
        self.account_dict = {}

        if self.user == "":
            self.user = getpass.getuser()

        self.query()

    def query(self):
        self.query_user_account_info()
        self.query_account_info()

    def query_user_account_info(self) -> list:
        output = execute_cmd("sacctmgr -P show user %s withassoc" % self.user)
        lines = output.split("\n")
        headers = lines[0].split("|")

        lines = lines[1:]

        account_dict = {}

        for line in lines:
            columns = line.split("|")
            if len(columns) > 1:
                account = columns[4]
                if account != "no_project":
                    partition = columns[5]
                    if not account in account_dict:
                        account_dict[account] = {}
                    if not 'partitions' in account_dict[account]:
                        account_dict[account]['partitions'] = []
                    account_dict[account]["partitions"].append(partition)

        self.user_account_dict = account_dict

    def query_account_info(self) -> dict:
        # sacctmgr -P show user
        output = execute_cmd("sacctmgr -P show user")
        lines = output.split("\n")
        headers = lines[0].split("|")
        lines = lines[1:]

        account_dict = {}

        for line in lines:
            columns = line.split("|")
            if len(columns) > 1:
                account = columns[1]
                user = columns[0]
                if not account in account_dict:
                    account_dict[account] = {}
                if not 'users' in account_dict[account]:
                    account_dict[account]['users'] = []
                account_dict[account]["users"].append(user)

        self.account_dict = account_dict

    def query_active_projects(self, user="") -> list:
        return list(self.user_account_dict.keys())
    
    def query_active_reservations(self) -> list:
        self.query_user_account_info()
        slurm = Slurm()
        reservations = slurm.query_reservations()
        print(reservations)
        projects = self.query_active_projects()
        print(projects)
        active_reservations = []
        for reservation in reservations:
            account = reservation["Accounts"]
            if account in projects:
                active_reservations.append(reservation["ReservationName"])

        return active_reservations



if __name__ == "__main__":

    account_mgr = AccountManager()
    print(account_mgr.query_active_reservations())

        
    #saccmgr = AccountManager()
    #saccmgr.query_user_account_info()

    #sacct = Accounting()
    #print(sacct.job_status)


