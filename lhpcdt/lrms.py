#!/bin/env python
"""Base classes for interacting with resource management systems."""

import os
import subprocess
import time
from subprocess import Popen, PIPE, STDOUT
import hostlist
import config

import jobs


def execute_cmd(cmd):
    """Wrapper function for calling an external process"""
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.stdout.read()
    retval = p.wait()
    return output


class GrantFile:
    """Class for accessing LUNARC grantfiles"""

    def __init__(self, filename):
        """Class constructor"""
        self.filename = filename

        self._parse_grantfile()

    def _parse_grantfile(self):
        """Parse grantfile"""

        f = open(self.filename, "r")
        lines = f.readlines()
        f.close()

        self.projects = {}

        for line in lines:
            items = line.split(",")
            if len(items)==6:
                name = items[0]
                self.projects[name] = {}
                self.projects[name]["start_date"] = items[1]
                self.projects[name]["end_date"] = items[2]
                self.projects[name]["core_hours"] = int(items[3])
                self.projects[name]["partition"] = items[4]
                self.projects[name]["pi"] = items[5].split("#")[0]
                self.projects[name]["users"] = items[5].split("#")[1].split()


class Queue(object):
    """Class for encapsuling a SLURM queue"""

    def __init__(self):
        """
        JOBID PARTITION		NAME	 USER	 STATE		 TIME TIMELIMIT	 NODES NODELIST(REASON)
        2981700		brand 5cpu.scr	 kurs16	 RUNNING 2-02:39:48 6-00:00:00		1 an225
        """
        self.squeueParams = ["jobid", "partition", "name", "user",
                             "state", "time", "timelimit", "nodes", "nodelist", "timeleft"]
        self.squeueFormat = "%.7i;%.9P;%.20j;%.8u;%.8T;%.10M;%.9l;%.6D;%R;%S"
        self.jobList = []
        self.jobs = {}
        self.userJobs = {}

    def job_info(self, jobid):
        """Return information on job jobid"""
        return execute_cmd('scontrol show job %s' % jobid)

    def update(self):
        """Update queue information"""
        output = execute_cmd(
            'squeue --long --noheader --format="%s"' % self.squeueFormat)
        lines = output.split("\n")

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
                for i in range(1, 10):
                    self.jobs[id][self.squeueParams[i]] = parts[i].strip()
                    job[self.squeueParams[i]] = parts[i].strip()

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

    def query_partitions(self):
        """Query partitions in slurm."""
        p = Popen("sinfo", stdout=PIPE, stderr=PIPE, shell=True)
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
                self.partitions.append(part_name)
                if part_name in self.node_lists:
                    self.node_lists[part_name] = self.node_lists[part_name] + hostlist.expand_hostlist(node_list)
                else:
                    self.node_lists[part_name] = hostlist.expand_hostlist(node_list)

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
        p = Popen("scontrol show node %s" % node, stdout=PIPE, stderr=PIPE, shell=True)
        scontrol_output = p.communicate()[0].split("\n")

        node_dict = {}

        for line in scontrol_output:
            var_pairs = line.strip().split(" ")
            if len(var_pairs) >= 1:
                for var_pair in var_pairs:
                    if len(var_pair)>0:
                        var_name = var_pair.split("=")[0]
                        var_value = var_pair.split("=")[1]
                        node_dict[var_name] = var_value

        return node_dict

    def query_features(self, part):
        """Query features of partition"""

        node_list = self.node_lists[part]

        feature_list =[]

        for node in node_list:
            node_info = self.query_node(node)

            features = node_info["AvailableFeatures"].split(",")
            feature_list.extend(features)

        return list(set(feature_list))

    def query_gres(self, part):
        """Query features of partition"""

        node_list = self.node_lists[part]

        gres_list =[]

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

        p = Popen("sbatch", stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
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
                  stdout=PIPE, stderr=PIPE, shell=True)
        squeue_output = p.communicate()[0].strip().split(";")

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
        result = subprocess.call("scancel %d" % (job.id), shell=True)
        job.id = -1
        job.status = ""
        return result

    def wait_for_start(self, job):
        """Wait for job to start"""
        self.job_status(job)

        while job.status != "R":
            time.sleep(1)
            self.job_status(job)

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
