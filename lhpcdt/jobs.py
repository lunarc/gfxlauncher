#!/bin/env python
"""Base job classes"""

import os
import sys
import subprocess
import time


class Job(object):
    """Class describing a SLURM jobs"""

    def __init__(self, account="", partition="", time="00:60:00"):
        """Initialise default class variables"""

        self.script = ""
        self.id = -1
        self.status = ""

        self.magic = "#!/bin/bash"
        self.name = "gui_interactive"
        self.nodes = ""
        self.tasksPerNode = 1
        self.exclusive = False
        self.time = time
        self.nodeCount = 1
        self.memory = -1
        self.account = account
        self.partition = partition
        self.node = ""
        self.submitNode = False

        self.scriptLines = []
        self.customLines = []

        self._create_script()

    def add_script(self, line):
        self.scriptLines.append(line)

    def add_option(self, option):
        self.add_script("#SBATCH " + option)

    def clear_script(self):
        self.scriptLines = []
        self.customLines = []

    def _create_script(self):

        self.scriptLines = []

        self.add_script(self.magic)
        self.add_script("")

        if self.account != "":
            self.add_option("-A %s" % self.account)

        if self.submitNode:
            self.add_option("-w %s" % self.node)
        else:
            if self.partition != "":
                self.add_option("-p %s" % self.partition)

        self.add_option("-N %d" % self.nodeCount)
        self.add_option("--ntasks-per-node=%d" % self.tasksPerNode)
        self.add_option("--time=%s" % self.time)

        if self.memory > 0:
            self.add_option("--mem=%d" % self.memory)

        if self.exclusive:
            self.add_option("--exclusive")

        self.add_option("-J %s" % self.name)
        self.add_script("")
        self.add_script('echo "Starting at `date`"')
        self.add_script('echo "Running on hosts: $SLURM_NODELIST"')
        self.add_script('echo "Running on $SLURM_NNODES nodes."')
        self.add_script('echo "Running on $SLURM_NPROCS processors."')
        self.add_script('echo "Current working directory is `pwd`"')
        self.add_script('')

        self.script = "\n".join(self.scriptLines + self.customLines)

    def add_custom_script(self, line):
        self.customLines.append(line)

    def update(self):
        self._create_script()

    def __str__(self):
        return self.script


class PlaceHolderJob(Job):
    """Placeholder job running acting as master process"""

    def __init__(self, account="", partition="", time="00:30:00"):
        Job.__init__(self, account, partition, time)
        self.add_custom_script('while true; do date; sleep 5; done')
        self.update()
