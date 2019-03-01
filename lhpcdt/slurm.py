#!/bin/env python

import os
import sys
import subprocess


def executeCmd(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = p.stdout.read()
    retval = p.wait()
    return output


class Queue(object):

    def __init__(self):
        """
        JOBID PARTITION		NAME	 USER	 STATE		 TIME TIMELIMIT	 NODES NODELIST(REASON)
        2981700		brand 5cpu.scr	 kurs16	 RUNNING 2-02:39:48 6-00:00:00		1 an225
        """
        self.squeueParams = ["jobid", "partition", "name", "user",
                             "state", "time", "timelimit", "nodes", "nodelist", "timeleft"]
        self.squeueFormat = "%.7i;%.9P;%.8j;%.8u;%.8T;%.10M;%.9l;%.6D;%R;%S"
        self.jobList = []
        self.jobs = {}
        self.userJobs = {}

    def jobInfo(self, jobid):
        return executeCmd('scontrol show job %s' % jobid)

    def update(self):
        output = executeCmd(
            'squeue --long --noheader --format="%s"' % self.squeueFormat)
        lines = output.split("\n")

        self.jobs = {}
        self.jobList = []

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


if __name__ == "__main__":

    q = Queue()
    q.update()
    print(q.jobList)
