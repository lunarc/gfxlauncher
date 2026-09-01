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
Jobs module

This module provides classes for supported job types.
"""


import os
import sys
import subprocess
import time
import urllib.parse as up

from subprocess import Popen, PIPE, STDOUT

def find_remote_port(url):
    """Extract port information from a url."""

    url_parts = up.urlparse(url)
    if url_parts.netloc.find(":")!=-1:
        return int(url_parts.netloc.split(":")[1])
    else:
        return -1


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
        self.cpusPerNode = -1
        self.exclusive = False
        self.time = time
        self.nodeCount = 1
        self.memory = -1
        self.account = account
        self.partition = partition
        self.reservation = ""
        self.node = ""
        self.submitNode = False
        self.constraints = []
        self.gres = ""
        self.oversubscribe = False
        self.module_list = []

        self.scriptLines = []
        self.customLines = []

        self._process_output = False
        self.update_processing = False

        self.processing_description = ""

        self.output = ""
        self.error = ""

        self._create_script()

    def add_constraint(self, constraint):
        """Add constraint (feature)"""
        self.constraints.append(constraint)

    def clear_constraints(self):
        self.constraints = []

    def add_script(self, line):
        self.scriptLines.append(line)

    def add_option(self, option):
        self.add_script("#SBATCH " + option)

    def add_module(self, name, version=""):
        self.module_list.append([name, version])

    def clear_script(self):
        self.scriptLines = []
        self.customLines = []
        self.constraints = []
        self.module_list = []

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

        if self.reservation != "":
            self.add_option("--reservation=%s" % self.reservation)

        if self.output != "":
            self.add_option("--output=%s" % self.output)

        if self.error != "":
            self.add_option("--error=%s" % self.error)

        if self.nodeCount >= 0:
            self.add_option("-N %d" % self.nodeCount)

        if self.tasksPerNode >= 0:
            self.add_option("--ntasks-per-node=%d" % self.tasksPerNode)

        self.add_option("--time=%s" % self.time)

        if self.gres != "":
            self.add_option("--gres=%s" % self.gres)

        if self.memory > 0:
            self.add_option("--mem=%d" % self.memory)

        if self.exclusive:
            self.add_option("--exclusive")

        if self.oversubscribe:
            self.add_option("--oversubscribe")

        if len(self.constraints) > 0:
            if len(self.constraints) == 1:
                self.add_option("--constraint=%s" % self.constraints[0])
            else:
                constraint_string = "&".join(self.constraints)
                self.add_option("--constraint=%s" % constraint_string)

        self.add_option("-J %s" % self.name)
        self.add_script("")
        self.add_script('echo "Starting at `date`"')
        self.add_script('echo "Running on hosts: $SLURM_NODELIST"')
        self.add_script('echo "Running on $SLURM_NNODES nodes."')
        self.add_script('echo "Running on $SLURM_NPROCS processors."')
        self.add_script('echo "SLURM JobID $SLURM_JOB_ID processors."')
        self.add_script('echo "Node has $SLURM_CPUS_ON_NODE processors."')
        self.add_script('echo "Node has $SLURM_MEM_PER_NODE total memory."')
        self.add_script('echo "Node has $SLURM_MEM_PER_CPU memory per cpu."')
        self.add_script('echo "Current working directory is `pwd`"')
        self.add_script('echo "Current path is $PATH"')
        self.add_script('')

        for module in self.module_list:
            module_name = module[0]
            module_version = module[1]

            if module_version == "":
                self.add_script('module load %s' % (module_name))
            else:
                self.add_script('module load %s/%s' % (module_name, module_version))

        self.script = "\n".join(self.scriptLines + self.customLines)

    def add_custom_script(self, line):
        self.customLines.append(line)

    def update(self):
        self._create_script()

    def set_process_output(self, flag):
        self._process_output = flag

    def get_process_output(self):
        return self._process_output

    def do_process_output(self, output_lines):
        pass

    def do_update_processing(self):
        pass

    def __str__(self):
        return self.script

    process_output = property(get_process_output, set_process_output)


class PlaceHolderJob(Job):
    """Placeholder job running acting as master process"""

    def __init__(self, account="", partition="", time="00:30:00"):
        Job.__init__(self, account, partition, time)
        self.add_custom_script('while true; do sleep 60; done')
        self.update()

conda_initialise_script = """# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!

if [ -z "${EBROOTANACONDA3}" ]; then
    echo "You need to load the Anaconda3 module before sourcing this script."
    return
fi

__conda_setup="$(${EBROOTANACONDA3}/bin/conda 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "${EBROOTANACONDA3}/etc/profile.d/conda.sh" ]; then
        . "${EBROOTANACONDA3}/etc/profile.d/conda.sh"
    else
        export PATH="${EBROOTANACONDA3}/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
"""

class JupyterJob(Job):
    """Shared implementation for Jupyter Notebook and JupyterLab jobs"""

    KIND_NOTEBOOK = "notebook"
    KIND_LAB = "lab"

    def __init__(self, kind, account="", partition="", time="00:30:00", module="Anaconda3", use_localhost=False, conda_env="", conda_source_env="", working_dir="", extra_args=""):
        Job.__init__(self, account, partition, time)

        self.kind = kind
        self.use_localhost = use_localhost
        self.notebook_url = ""
        self.process_output = True
        self.processing_description = "Waiting for notebook instance to start."
        self.module = module

        self.conda_source_env = conda_source_env
        self.conda_env = conda_env
        self.working_dir = working_dir
        self.extra_args = extra_args

        if ',' in self.module:
            modules = self.module.split(",")
            for module in modules:
                self.add_module(module.strip())
        else:
            self.add_module(self.module)

        self.add_custom_script("unset XDG_RUNTIME_DIR")

        if self.conda_source_env != "":
            self.add_custom_script("source %s" % self.conda_source_env)

        if self.conda_env != "":
            self.add_custom_script("conda activate %s" % self.conda_env)

        if self.working_dir != "":
            self.add_custom_script('cd "%s"' % self.working_dir)

        command = 'jupyter-lab' if self.kind == self.KIND_LAB else 'jupyter-notebook'

        if self.use_localhost:
            command += ' --no-browser'
        else:
            command += ' --no-browser --ip=$HOSTNAME'

        if self.extra_args != "":
            command += ' %s' % self.extra_args

        self.add_custom_script(command)

        self.add_custom_script("module list")
        self.add_custom_script("which python")

    def on_notebook_url_found(self, url):
        """Event method called when notebook has been found"""
        label = "Lab" if self.kind == self.KIND_LAB else "Notebook"
        print("%s found: %s" % (label, url))

    def do_process_output(self, output_lines):
        """Process job output"""

        Job.do_process_output(self, output_lines)

        if self.process_output:
            for line in output_lines:
                if line.find("?token=") != -1:
                    if line.find("127.0.0.1") == -1:
                        url = line[line.find("http:"):].strip()
                        port = find_remote_port(url)
                        if port != -1:
                            self.notebook_port = port
                        else:
                            self.notebook_port = 8888
                        self.notebook_url = url
                        self.process_output = False
                        self.on_notebook_url_found(self.notebook_url)


class JupyterNotebookJob(JupyterJob):
    """Jupyter notebook job"""

    def __init__(self, account="", partition="", time="00:30:00", notebook_module="Anaconda3", use_localhost=False, conda_env="", conda_source_env="", working_dir="", extra_args=""):
        JupyterJob.__init__(self, JupyterJob.KIND_NOTEBOOK, account, partition, time,
                             notebook_module, use_localhost, conda_env, conda_source_env, working_dir, extra_args)


class JupyterLabJob(JupyterJob):
    """Jupyter lab job"""

    def __init__(self, account="", partition="", time="00:30:00", jupyterlab_module="Anaconda3", use_localhost=False, conda_env="", conda_source_env="", working_dir="", extra_args=""):
        JupyterJob.__init__(self, JupyterJob.KIND_LAB, account, partition, time,
                             jupyterlab_module, use_localhost, conda_env, conda_source_env, working_dir, extra_args)


class RStudioJob(Job):
    """RStudio Server job"""

    def __init__(self, account="", partition="", time="00:30:00", rstudio_module="rserver/4.4.2", conda_env="", conda_source_env="", working_dir="", extra_args=""):
        Job.__init__(self, account, partition, time)

        # Always tunnel-only, not configurable: the command below runs
        # with --auth-none=1 (no login at all), so this must never be
        # reachable directly on the node's network interface - only via
        # the SSH tunnel launcher.py sets up when it sees
        # use_localhost=True on the job.
        self.use_localhost = True
        self.notebook_url = ""
        self.process_output = True
        self.processing_description = "Waiting for RStudio Server instance to start."
        self.rstudio_module = rstudio_module

        self.conda_source_env = conda_source_env
        self.conda_env = conda_env
        self.working_dir = working_dir
        self.extra_args = extra_args

        if ',' in self.rstudio_module:
            modules = self.rstudio_module.split(",")
            for module in modules:
                self.add_module(module.strip())
        else:
            self.add_module(self.rstudio_module)

        self.add_custom_script("unset XDG_RUNTIME_DIR")

        if self.conda_source_env != "":
            self.add_custom_script("source %s" % self.conda_source_env)

        if self.conda_env != "":
            self.add_custom_script("conda activate %s" % self.conda_env)

        if self.working_dir != "":
            self.add_custom_script('cd "%s"' % self.working_dir)

        self.add_custom_script('RSTUDIO_PORT=$(python3 -c \'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()\')')

        bind_address = "127.0.0.1"

        command = 'rserver --www-address=%s --www-port=$RSTUDIO_PORT --auth-none=1' % bind_address

        if self.extra_args != "":
            command += ' %s' % self.extra_args

        self.add_custom_script(command + ' &')
        self.add_custom_script('RSERVER_PID=$!')
        self.add_custom_script('while ! (echo > /dev/tcp/%s/$RSTUDIO_PORT) 2>/dev/null; do sleep 1; done' % bind_address)
        # "localhost", not $HOSTNAME: launcher.py's tunnel setup only
        # rewrites the *port* in this URL to the local tunnel port - it
        # relies on the hostname already being "localhost", the same
        # convention Jupyter follows by reporting its own bind address
        # rather than the node's real hostname. Reporting the real
        # hostname here instead would silently point the browser at the
        # node directly, bypassing the tunnel it just set up.
        self.add_custom_script('echo "RSTUDIO_URL: http://localhost:$RSTUDIO_PORT/"')

        self.add_custom_script("module list")
        self.add_custom_script('wait $RSERVER_PID')

    def on_notebook_url_found(self, url):
        """Event method called when the RStudio Server URL has been found"""
        print("RStudio Server found: %s" % url)

    def do_process_output(self, output_lines):
        """Process job output"""

        Job.do_process_output(self, output_lines)

        if self.process_output:
            for line in output_lines:
                if line.find("RSTUDIO_URL:") != -1:
                    url = line[line.find("http:"):].strip()
                    port = find_remote_port(url)
                    if port != -1:
                        self.notebook_port = port
                    else:
                        self.notebook_port = 8787
                    self.notebook_url = url
                    self.process_output = False
                    self.on_notebook_url_found(self.notebook_url)


class OllamaChatJob(Job):
    """Ollama + Open WebUI chat job"""

    def __init__(self, account="", partition="", time="01:00:00",
                 ollama_module="ollama/0.32.14", model="llama3.1:8b",
                 models_dir="", extra_args=""):
        Job.__init__(self, account, partition, time)

        # Tunnel-only, unconditionally, as a second layer on top of Open
        # WebUI's own login (WEBUI_AUTH=True): containers/ollama-chat/bin/
        # ollama-chat provisions the single per-user account itself via
        # Open WebUI's signup API the instant its port opens - before this
        # job ever prints a URL for gfxlauncher to act on - then disables
        # further signups for the rest of the job's life. See that script's
        # header and containers/ollama-chat/README.md for the full
        # rationale, including the residual race this can shrink but not
        # provably eliminate on a non-exclusive node allocation.
        self.use_localhost = True
        self.notebook_url = ""
        self.process_output = True
        # Kept short (unlike a fuller explanation) so it fits the fixed-width
        # status bar at the bottom of the launcher window alongside the
        # elapsed-seconds suffix launcher.py appends to it - the download
        # progress bar carries the fuller "why is this slow" explanation
        # during the actual pull.
        self.processing_description = "Waiting for chat interface to start (first launch may be slow)."
        self.ollama_module = ollama_module
        self.model = model
        self.models_dir = models_dir
        self.extra_args = extra_args
        self.pull_progress = 0

        self.add_module(self.ollama_module)
        self.add_custom_script("unset XDG_RUNTIME_DIR")

        if self.models_dir != "":
            self.add_custom_script('export OLLAMA_MODELS_DIR="%s"' % self.models_dir)

        self.add_custom_script('OLLAMA_PORT=$(python3 -c \'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()\')')
        self.add_custom_script('WEBUI_PORT=$(python3 -c \'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()\')')

        command = 'ollama-chat --ollama-port=$OLLAMA_PORT --webui-port=$WEBUI_PORT --model "%s"' % self.model

        if self.extra_args != "":
            command += ' %s' % self.extra_args

        self.add_custom_script(command)
        self.add_custom_script("module list")

    def on_notebook_url_found(self, url):
        """Event method called when the chat interface URL has been found"""
        print("Chat interface found: %s" % url)

    def on_pull_progress(self, percent):
        """Event method called as the model download progresses (0-100)"""
        print("Model download: %d%%" % percent)

    def on_account_created(self, email):
        """Event method called when the job has just provisioned a fresh
        Open WebUI account (never called on a run that reused an existing
        one - see containers/ollama-chat/bin/ollama-chat)."""
        print("Chat account created: %s" % email)

    def do_process_output(self, output_lines):
        """Process job output"""

        Job.do_process_output(self, output_lines)

        if self.process_output:
            for line in output_lines:
                if line.find("OLLAMA_PULL_PROGRESS:") != -1:
                    try:
                        pct = int(line.split("OLLAMA_PULL_PROGRESS:")[1].strip())
                    except ValueError:
                        continue
                    if pct != self.pull_progress:
                        self.pull_progress = pct
                        self.on_pull_progress(pct)
                elif line.find("OLLAMA_CHAT_ACCOUNT_CREATED:") != -1:
                    email = line.split("OLLAMA_CHAT_ACCOUNT_CREATED:")[1].strip()
                    self.on_account_created(email)
                elif line.find("OLLAMA_CHAT_URL:") != -1:
                    url = line[line.find("http:"):].strip()
                    port = find_remote_port(url)
                    if port != -1:
                        self.notebook_port = port
                    else:
                        self.notebook_port = 8080
                    self.notebook_url = url
                    self.process_output = False
                    self.on_notebook_url_found(self.notebook_url)


class CodeModelJob(Job):
    """Ollama code-model job exposing a native API for IDE plugins (e.g.
    VS Code's Continue extension), with no chat frontend."""

    def __init__(self, account="", partition="", time="01:00:00",
                 codemodel_module="ollama/0.32.14", model="qwen2.5-coder:7b",
                 models_dir="", extra_args=""):
        Job.__init__(self, account, partition, time)

        # Tunnel-only, unconditionally - Ollama has no authentication of its
        # own, so the SSH tunnel is the only access gate. Same rationale as
        # OllamaChatJob/RStudioJob above.
        self.use_localhost = True
        self.notebook_url = ""
        self.process_output = True
        self.processing_description = "Waiting for code model to start (first launch may be slow)."
        self.codemodel_module = codemodel_module
        self.model = model
        self.models_dir = models_dir
        self.extra_args = extra_args
        self.pull_progress = 0

        self.add_module(self.codemodel_module)
        self.add_custom_script("unset XDG_RUNTIME_DIR")

        if self.models_dir != "":
            self.add_custom_script('export OLLAMA_MODELS_DIR="%s"' % self.models_dir)

        self.add_custom_script('OLLAMA_PORT=$(python3 -c \'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()\')')

        command = 'ollama-code-api --ollama-port=$OLLAMA_PORT --model "%s"' % self.model

        if self.extra_args != "":
            command += ' %s' % self.extra_args

        self.add_custom_script(command)
        self.add_custom_script("module list")

    def on_notebook_url_found(self, url):
        """Event method called when the code model's API endpoint has been found"""
        print("Code model endpoint found: %s" % url)

    def on_pull_progress(self, percent):
        """Event method called as the model download progresses (0-100)"""
        print("Model download: %d%%" % percent)

    def do_process_output(self, output_lines):
        """Process job output"""

        Job.do_process_output(self, output_lines)

        if self.process_output:
            for line in output_lines:
                if line.find("OLLAMA_PULL_PROGRESS:") != -1:
                    try:
                        pct = int(line.split("OLLAMA_PULL_PROGRESS:")[1].strip())
                    except ValueError:
                        continue
                    if pct != self.pull_progress:
                        self.pull_progress = pct
                        self.on_pull_progress(pct)
                elif line.find("CODE_MODEL_URL:") != -1:
                    url = line[line.find("http:"):].strip()
                    port = find_remote_port(url)
                    if port != -1:
                        self.notebook_port = port
                    else:
                        self.notebook_port = 11434
                    self.notebook_url = url
                    self.process_output = False
                    self.on_notebook_url_found(self.notebook_url)


class VMJob(Job):
    """Special Job for starting VM:s"""

    def __init__(self, account="", partition="", time="00:30:00"):
        """Class constructor"""
        super().__init__(account, partition, time)
        self.notebook_url = ""
        self.process_output = False
        self.processing_description = "Waiting Windows session to become available."
        self.update_processing = True
        #self.add_custom_script("sleep infinity")
        self.add_custom_script("while true; do date; sleep 5; done")
        self.hostname = ""
        self.oversubscribe = True
        self.memory = 100
        self.gres = "win10m"
        self.nodeCount = -1
        self.tasksPerNode = -1

    def do_update_processing(self):
        """Check for vm job ip file"""

        home_dir = os.getenv("HOME")

        store_dir = os.path.join(home_dir, ".lhpc")
        job_host_filename = os.path.join(
            store_dir, "vm_host_%s.ip" % str(self.id))

        if os.path.exists(job_host_filename):
            with open(job_host_filename) as f:
                hostname = f.readlines()[0].strip()

            self.update_processing = False
            self.hostname = hostname
            self.on_vm_available(hostname)

    def on_vm_available(self, hostname):
        """Callback when job ib file found."""
        print("VM vailable: "+hostname)

class JobPluginBase(Job):
    """Base class for loadable job plugins."""
    def __init__(self, account="", partition="", time="00:60:00"):
        """Class constructor"""

        super().__init__(account, partition, time)
        self.plugin_name = "Noname"
        self.plugin_descr = "Plugin that does nothing"
