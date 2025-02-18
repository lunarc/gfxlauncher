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
import re

import subprocess
import time
import re
import select
import json
import signal


def run_jupyter_notebook_and_wait_for_url(timeout=60, port=None, notebook_dir=None):
    """
    Execute a Jupyter notebook server via conda, wait for the URL to appear, then keep it running.
    
    Args:
        timeout: Maximum time in seconds to wait for the URL
        port: Specific port to run Jupyter on (optional)
        notebook_dir: Directory to start Jupyter in (optional)
    
    Returns:
        process: The running Jupyter process object
        url_info: Dictionary containing URL components
    """
    # Build the command
    command = ["conda", "run", "--no-capture-output", "-n", "numpy-env", "jupyter", "lab", "--no-browser"]
    if port:
        command.extend(["--port", str(port)])
    if notebook_dir:
        command.extend(["--notebook-dir", notebook_dir])
    
    # Pattern to match Jupyter notebook URL
    url_pattern = r'(https?://)(localhost|127\.0\.0\.1)(:(\d+))?(/lab\??)(token=([a-zA-Z0-9]+))?'
    
    print(f"Starting Jupyter notebook server with command: {' '.join(command)}")
    
    # Start the process with pipes for stdout and stderr
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,  # Unbuffered
        universal_newlines=False  # Binary mode
    )
    
    # Compile the regex pattern
    pattern = re.compile(url_pattern)
    
    # Track the start time for timeout calculation
    start_time = time.time()
    stdout_buffer = b""
    stderr_buffer = b""
    
    print(f"Waiting for Jupyter Lab to start (timeout: {timeout}s)...")
    
    # Keep checking the output until we find the URL or time out
    while time.time() - start_time < timeout:
        # Check if process has terminated unexpectedly
        poll_result = process.poll()
        if poll_result is not None:
            print(f"Process terminated with exit code: {poll_result}")
            # Try to read any final output
            stdout_buffer += process.stdout.read() or b""
            stderr_buffer += process.stderr.read() or b""
            raise RuntimeError(f"Jupyter notebook process terminated unexpectedly with code {process.returncode}")
        
        # Use select to wait for data with a timeout (prevents blocking)
        ready_to_read, _, _ = select.select(
            [process.stdout, process.stderr], 
            [], 
            [], 
            0.5  # 500ms timeout
        )
        
        # Read from streams that have data
        for stream in ready_to_read:
            if stream == process.stdout:
                data = stream.read(1024)  # non-blocking because of select
                if data:
                    stdout_buffer += data
                    try:
                        print(f"STDOUT: {data.decode('utf-8', errors='replace').strip()}")
                    except:
                        print(f"STDOUT: [binary data, length {len(data)}]")
            elif stream == process.stderr:
                data = stream.read(1024)  # non-blocking because of select
                if data:
                    stderr_buffer += data
                    try:
                        print(f"STDERR: {data.decode('utf-8', errors='replace').strip()}")
                    except:
                        print(f"STDERR: [binary data, length {len(data)}]")
        
        # Check both buffers for URL pattern
        for buffer_name, buffer_content in [("stdout", stdout_buffer), ("stderr", stderr_buffer)]:
            try:
                # Convert binary buffer to string for regex matching
                buffer_str = buffer_content.decode('utf-8', errors='replace')
                match = pattern.search(buffer_str)
                if match:
                    # Extract the components
                    protocol = match.group(1)                    
                    hostname = match.group(2)                    
                    port_with_colon = match.group(3) or ""       
                    port_number = match.group(4) or "8888"       
                    lab_path = match.group(5) or "/lab"          
                    token_param = match.group(6) or ""           
                    token = match.group(7) or ""                 
                    
                    # Construct the complete URL
                    if token and not token_param.startswith("token="):
                        token_param = f"token={token}"
                    
                    # Ensure lab_path ends with ? if we have a token
                    if token and not lab_path.endswith("?"):
                        lab_path = f"{lab_path}?"
                    elif not token and lab_path.endswith("?"):
                        lab_path = lab_path[:-1]
                    
                    complete_url = f"{protocol}{hostname}{port_with_colon}{lab_path}"
                    if token:
                        complete_url += token_param
                    
                    # Create URL info dictionary
                    url_info = {
                        'complete_url': complete_url,
                        'base_url': f"{protocol}{hostname}",
                        'port': int(port_number),
                        'token': token,
                        'lab_path': lab_path.rstrip('?')
                    }
                    
                    print(f"\nFound Jupyter Lab URL:")
                    print(f"  Complete URL: {url_info['complete_url']}")
                    print(f"  Base URL: {url_info['base_url']}")
                    print(f"  Port: {url_info['port']}")
                    print(f"  Token: {url_info['token']}")
                    
                    return process, url_info
            except Exception as e:
                print(f"Error processing {buffer_name} buffer: {e}")
        
        # A small sleep is still needed to prevent CPU spinning
        time.sleep(0.1)
    
    # If we get here, we timed out waiting for the URL
    print("Timeout reached, terminating process...")
    try:
        process.terminate()
        process.wait(timeout=5)
    except:
        process.kill()
        
    # Print any accumulated output for debugging
    print("\nLast stdout output:")
    print(stdout_buffer.decode('utf-8', errors='replace'))
    print("\nLast stderr output:")
    print(stderr_buffer.decode('utf-8', errors='replace'))
    
    raise TimeoutError(f"Timed out after {timeout}s waiting for Jupyter Lab URL")


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

    def run(self):
        self.status = "starting"
        try:
            self.process, self.urlinfo = run_jupyter_notebook_and_wait_for_url()
            self.url = self.urlinfo['complete_url']
            self.port = self.urlinfo['port']
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
            self.process.terminate()
            self.status = "cancelled"
            return True
        else:
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
        for job_id in self.queue.keys():
            job = self.queue[job_id]
            print("%d;%s;%s;%s" % (job_id, job.name, job.status, job.url))    

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
                "pid": job.pid
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
                self.queue[int(job_id)] = job

        
if __name__ == "__main__":

    job = NotebookJob("Test")

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
    

