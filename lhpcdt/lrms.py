#!/bin/env python

import os
import sys
import subprocess
import time
from subprocess import Popen, PIPE, STDOUT
import hostlist

import jobs


def execute_cmd(cmd):
    """Wrapper function for calling an external process"""
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.stdout.read()
    retval = p.wait()
    return output


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
                if not self.jobs.has_key(id):
                    self.jobs[id] = {}
                    job = {"jobid": id}
                for i in range(1, 10):
                    self.jobs[id][self.squeueParams[i]] = parts[i].strip()
                    job[self.squeueParams[i]] = parts[i].strip()

                self.jobList.append(job)

                if not self.userJobs.has_key(self.jobs[id]["user"]):
                    self.userJobs[self.jobs[id]["user"]] = {}

                self.userJobs[self.jobs[id]["user"]][id] = self.jobs[id]


class Slurm(object):
    """SLURM Interface class"""

    def __init__(self):
        """Slurm constructor"""
        self.partitions = []
        self.nodeLists = {}

    def query_partitions(self):
        """Query partitions in slurm."""
        p = Popen("sinfo", stdout=PIPE, stderr=PIPE, shell=True)
        squeueOutput = p.communicate()[0].split("\n")

        self.partitions = []
        self.nodeLists = {}

        partLines = squeueOutput[1:]

        for line in partLines:
            if line != "":
                partName = line.split()[0].strip()
                nodeList = line.split()[5]
                if partName.find("*") != -1:
                    partName = partName[:-1]
                self.partitions.append(partName)
                self.nodeLists[partName] = hostlist.expand_hostlist(nodeList)

        self.partitions = list(set(self.partitions))

    def submit(self, job):
        """Submit job to SLURM"""
        p = Popen("sbatch", stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        sbatchOutput = p.communicate(input=job.script)[0].strip()
        if sbatchOutput.find("Submitted batch") != -1:
            job.id = int(sbatchOutput.split()[3])
            return True
        else:
            job.id = -1
            return False

    def job_status(self, job):
        """Query status of job"""
        p = Popen("squeue -j " + str(job.id) + " -t PD,R -h -o '%t;%N;%L;%M;%l'",
                  stdout=PIPE, stderr=PIPE, shell=True)
        squeueOutput = p.communicate()[0].strip().split(";")

        if len(squeueOutput) > 1:
            job.status = squeueOutput[0]
            job.nodes = squeueOutput[1]
            job.timeLeft = squeueOutput[2]
            job.timeRunning = squeueOutput[3]
            job.timeLimit = squeueOutput[4]
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
