#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2025 LUNARC, Lund University
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
"""

import os, sys, subprocess, json, copy

import subprocess
import time

import subprocess
import time

import json
import signal

from lhpcdt.launch_utils import *

class LocalNotebookJob(object):
    def __init__(self, name):
        self.id = -1
        self.name = name
        self.cmdline = ""
        self.process = None
        self.status = "waiting"
        self.stdout = ""
        self.stderr = ""
        self.url = ""
        self.port = 0
        self.pid = 0
        self.notebook_env = ""
        self.walltime = "00:30:00"
        self.tasks_per_node = 1

    def run(self):
        self.status = "starting"
        try:
            self.process, self.urlinfo, child_pid = run_jupyter_notebook_and_wait_for_url()
            self.url = self.urlinfo['complete_url']
            self.port = self.urlinfo['port']
            self.child_pid = child_pid
            self.pid = self.process.pid
            self.status = "running"
        except Exception as e:
            self.status = "error"
            self.stderr = str(e)
            print("Error starting notebook: %s" % str(e))

    def status(self):
        if self.process is None:
            return "waiting"
        if self.process.poll() is None:
            return "running"
        else:
            return "finished"

    def cancel(self):

        if self.process is not None:
            cleanup_processes(self.process, self.child_pid)
            self.status = "cancelled"
            return True
        else:
            if self.child_pid != 0:
                try:
                    os.kill(self.child_pid, signal.SIGTERM)
                    self.status = "cancelled"
                except:
                    pass

            if self.pid != 0:
                try:
                    os.kill(self.pid, signal.SIGTERM)
                    self.status = "cancelled"
                    return True
                except:
                    pass
            
            return True
        
        
    def wait(self):
        if (self.process is not None) and (self.process.poll() is None):
            self.process.wait()
        self.status = "finished"


class LocalQueue(object):
    def __init__(self):
        self.queue = {}
        
    def submit(self, job):
        queue_job = copy.copy(job)
        queue_job.id = len(self.queue)
        self.queue[queue_job.id] = queue_job
        queue_job.run()
        return queue_job.id
    
    def has_job(self, job_id):
        return job_id in self.queue

    def status(self, job_id):
        if job_id not in self.queue:
            return "not found"
        else:
            return self.queue[job_id].status()
    
    def cancel(self, job_id):
        if job_id not in self.queue:
            return False
        
        job = self.queue[job_id]
        if job.cancel():
            del self.queue[job_id]
            return True
        else:
            return False
        
    def cancel_all(self):
        to_delete = []
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            to_delete.append(job_id)
            job.cancel()

        for job_id in to_delete:
            del self.queue[job_id]

        
    def list(self):
        return self.queue.keys()
    
    def print(self):
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            print("Job ID: %d, Name: %s, Status: %s, URL: %s" % (job_id, job.name, job.status, job.url))

    def job_table(self):
        print(">>>")
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            print("%d;%s;%s;%s" % (job_id, job.name, job.status, job.url))
        print("<<<")

    def wait(self):
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            job.wait()

    def save_state(self, filename):
        state = {}
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            state[job_id] = {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "url": job.url,
                "port": job.port,
                "pid": job.pid,
                "child_pid": job.child_pid,
                "notebook_env": job.notebook_env,
                "walltime": job.walltime,
                "tasks_per_node": job.tasks_per_node
            }
        with open(filename, "w") as f:
            json.dump(state, f)

    def load_state(self, filename):
        with open(filename, "r") as f:
            state = json.load(f)
            for job_id in state.keys():
                job = LocalNotebookJob(state[job_id]['name'])
                job.id = int(state[job_id]['id'])
                job.status = state[job_id]['status']
                job.url = state[job_id]['url']
                job.port = int(state[job_id]['port'])
                job.pid = int(state[job_id]['pid'])
                job.child_pid = int(state[job_id]['child_pid'])
                job.notebook_env = state[job_id]['notebook_env']
                job.walltime = state[job_id]['walltime']
                job.tasks_per_node = state[job_id]['tasks_per_node']
                self.queue[int(job_id)] = job

        
if __name__ == "__main__":

    job = LocalNotebookJob("Test")

    queue = LocalQueue()

    job_id = queue.submit(job)
    queue.print()

    for i in range(10):
        print("Waiting...")
        time.sleep(1)
        queue.print()

    queue.cancel(job_id)
    queue.print()
    queue.wait()
    

