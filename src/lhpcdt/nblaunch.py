#!/usr/bin/env python3
import cmd
import subprocess
import json
import re
from dataclasses import dataclass
from typing import Optional, List, Dict
import shlex
import sys
from pathlib import Path

@dataclass
class NotebookJob:
    job_id: str
    notebook_path: str
    port: int
    status: str
    hostname: Optional[str] = None
    url: Optional[str] = None
    token: Optional[str] = None
    runtime: Optional[str] = None



class NotebookController(cmd.Cmd):
    """Interactive shell for managing Jupyter notebooks on SLURM."""
    
    intro = 'Welcome to the Notebook Controller. Type help or ? to list commands.\n'
    prompt = 'notebook> '
    
    def __init__(self):
        super().__init__()
        self.active_jobs: Dict[str, NotebookJob] = {}
        # Load any existing jobs from state file
        self.load_state()

    def _get_jupyter_token(self, job_id: str) -> Optional[str]:
        """Extract Jupyter token from the job's log file."""
        log_file = Path(f"jupyter-lab-{job_id}.log")
        if not log_file.exists():
            return None
            
        try:
            log_content = log_file.read_text()
            # Look for the token in the log file
            match = re.search(r'http://[^?]+\?token=([a-f0-9]+)', log_content)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error reading log file: {e}")
        return None
        

    def load_state(self):
        """Load saved job state from file."""
        state_file = Path.home() / '.notebook_controller_state'
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                    self.active_jobs = {
                        job_id: NotebookJob(**job_data)
                        for job_id, job_data in state.items()
                    }
            except Exception as e:
                print(f"Error loading state: {e}")

    def save_state(self):
        """Save current job state to file."""
        state_file = Path.home() / '.notebook_controller_state'
        try:
            with open(state_file, 'w') as f:
                state = {
                    job_id: {
                        'job_id': job.job_id,
                        'notebook_path': job.notebook_path,
                        'port': job.port,
                        'status': job.status,
                        'runtime': job.runtime,
                        'hostname': job.hostname,
                        'url': job.url,
                        'token': job.token
                    }
                    for job_id, job in self.active_jobs.items()
                }
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def do_submit(self, arg):
        """
        Submit a new Jupyter Lab job to SLURM.
        Usage: submit
        """
        # Find an available port
        port = self._find_free_port()
        
        # Create SLURM submission script
        submit_script = self._create_submission_script(port)
        
        try:
            # Submit job to SLURM
            result = subprocess.run(['sbatch'], input=submit_script,
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract job ID from sbatch output
                job_id = re.search(r'Submitted batch job (\d+)', result.stdout).group(1)
                
                # Record job
                self.active_jobs[job_id] = NotebookJob(
                    job_id=job_id,
                    notebook_path="",
                    port=port,
                    status='PENDING',
                    hostname=None,
                    token=None,
                    url=None
                )
                self.save_state()
                
                print(f"Submitted job {job_id} on port {port}")
            else:
                print(f"Error submitting job: {result.stderr}")
        
        except Exception as e:
            print(f"Error submitting job: {e}")

    def _create_submission_script(self, port: int) -> str:
        """Create SLURM submission script for running Jupyter notebook."""
        return f"""#!/bin/bash
#SBATCH --job-name=jupyter-lab
#SBATCH --output=jupyter-lab-%j.log
#SBATCH --time=8:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH -A lu-test

# Load any required modules
ml Anaconda3

# Get the hostname of the compute node
export HOSTNAME=$(hostname -f)

# Start Jupyter lab server
jupyter lab --ip=0.0.0.0 --port={port} &

# Save hostname to a file that can be read by the controller
echo $HOSTNAME > ~/.notebook_${{SLURM_JOB_ID}}_hostname

# Wait for the notebook to be ready
sleep infinity
"""

    def do_status(self, arg):
        """
        Check status of notebook jobs.
        Usage: status [job_id]
        """
        if not self.active_jobs:
            print("No active jobs")
            return

        if arg:
            # Check specific job
            job_id = arg.strip()
            if job_id not in self.active_jobs:
                print(f"No job found with ID {job_id}")
                return
            
            self._update_job_status(job_id)
            job = self.active_jobs[job_id]
            print(f"Job {job_id}:")
            print(f"  Notebook: {job.notebook_path}")
            print(f"  Port: {job.port}")
            print(f"  Status: {job.status}")
            if job.hostname:
                print(f"  Hostname: {job.hostname}")
                if job.url:
                    print(f"  URL: {job.url}")
                else:
                    print("  URL: Waiting for Jupyter token...")
            if job.runtime:
                print(f"  Runtime: {job.runtime}")
        else:
            # Check all jobs
            self._update_all_job_statuses()
            for job_id, job in self.active_jobs.items():
                print(f"Job {job_id}:")
                print(f"  Notebook: {job.notebook_path}")
                print(f"  Port: {job.port}")
                print(f"  Status: {job.status}")
                if job.hostname:
                    print(f"  Hostname: {job.hostname}")
                    if job.url:
                        print(f"  URL: {job.url}")
                    else:
                        print("  URL: Waiting for Jupyter token...")
                if job.runtime:
                    print(f"  Runtime: {job.runtime}")

    def do_job_table(self, arg):
        """Print a table of all active jobs."""
        if not self.active_jobs:
            return

        self._update_all_job_statuses()

        print("JobID;Port;Status;Hostname;URL;Runtime")
        for job in self.active_jobs.values():
            print(f"{job.job_id};{job.port};{job.status};{job.hostname};{job.url};{job.runtime}")

    def _update_job_status(self, job_id: str):
        """Update status for a specific job."""
        try:
            result = subprocess.run(['squeue', '-j', job_id, '-o', '%T %M %N'],
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse squeue output
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header line
                    status, runtime, node = lines[1].split()
                    job = self.active_jobs[job_id]
                    job.status = status
                    job.runtime = runtime

                    # Update hostname and URL if the job is running and we don't have them yet
                    if status == 'RUNNING':
                        if not job.hostname:
                            hostname_file = Path.home() / f'.notebook_{job_id}_hostname'
                            if hostname_file.exists():
                                job.hostname = hostname_file.read_text().strip()
                        
                        # Try to get token if we don't have it yet
                        if not job.token:
                            job.token = self._get_jupyter_token(job_id)
                            
                        # Update URL with token if we have all the information
                        if job.hostname and job.token:
                            job.url = f'http://{job.hostname}:{job.port}/?token={job.token}'

                else:
                    # Job not in queue, check if it completed
                    sacct_result = subprocess.run(
                        ['sacct', '-j', job_id, '-o', 'State', '-n'],
                        capture_output=True, text=True
                    )
                    if sacct_result.returncode == 0:
                        status = sacct_result.stdout.strip()
                        if 'COMPLETED' in status:
                            self.active_jobs[job_id].status = 'COMPLETED'
                        else:
                            self.active_jobs[job_id].status = 'FAILED'

                        self.active_jobs[job_id].url = ''
                        self.active_jobs[job_id].token = ''
            
            self.save_state()
            
        except Exception as e:
            print(f"Error updating job status: {e}")

    def _update_all_job_statuses(self):
        """Update status for all tracked jobs."""
        for job_id in list(self.active_jobs.keys()):
            self._update_job_status(job_id)

    def do_cancel(self, arg):
        """
        Cancel a notebook job.
        Usage: cancel <job_id>
        """
        if not arg:
            print("Error: job ID required")
            return

        job_id = arg.strip()
        if job_id not in self.active_jobs:
            print(f"No job found with ID {job_id}")
            return

        try:
            result = subprocess.run(['scancel', job_id], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Cancelled job {job_id}")
                self.active_jobs[job_id].status = 'CANCELLED'
                self.save_state()
            else:
                print(f"Error cancelling job: {result.stderr}")
        
        except Exception as e:
            print(f"Error cancelling job: {e}")

    def _find_free_port(self) -> int:
        """Find a free port number."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def do_quit(self, arg):
        """Exit the application."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        """Exit on EOF (Ctrl+D)."""
        print()
        return self.do_quit(arg)
    
    def do_clean_all(self, arg):
        """Clean up all jobs."""
        for job_id in list(self.active_jobs.keys()):
            self.do_cancel(job_id)

        for job_id in list(self.active_jobs.keys()):
            del self.active_jobs[job_id]

        state_file = Path.home() / '.notebook_controller_state'
        if state_file.exists():
            state_file.unlink()
            print("Cleared all jobs")

        self.save_state()

    def do_cancel_all(self, arg):
        """Cancel all jobs."""
        for job_id in list(self.active_jobs.keys()):
            self.do_cancel(job_id)


def main():
    NotebookController().cmdloop()        

if __name__ == '__main__':
    main()