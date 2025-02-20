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

import select, subprocess, re, time, psutil

def run_jupyter_notebook_and_wait_for_url(timeout=60, port=None, notebook_dir=None, verbose=False):
    """
    Execute a Jupyter notebook server via conda, wait for the URL to appear, then keep it running.
    
    Args:
        timeout: Maximum time in seconds to wait for the URL
        port: Specific port to run Jupyter on (optional)
        notebook_dir: Directory to start Jupyter in (optional)
    
    Returns:
        process: The running Jupyter process object
        url_info: Dictionary containing URL components
        child_pid: The PID of the actual Jupyter process (not the conda wrapper)
    """
    # Build the command
    command = ["conda", "run", "--no-capture-output", "-n", "numpy-env", "jupyter", "lab", "--no-browser"]
    if port:
        command.extend(["--port", str(port)])
    if notebook_dir:
        command.extend(["--notebook-dir", notebook_dir])
    
    # Pattern to match Jupyter notebook URL
    url_pattern = r'(https?://)(localhost|127\.0\.0\.1)(:(\d+))?(/lab\??)(token=([a-zA-Z0-9]+))?'
    
    if verbose:
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
    pid_pattern = re.compile(r'Jupyter\s+Lab\s+[\d\.]+\s+is\s+running\s+at.*?pid=(\d+)')
    
    # Track the start time for timeout calculation
    start_time = time.time()
    stdout_buffer = b""
    stderr_buffer = b""
    child_pid = None
    
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
                data = stream.read(1024)
                if data:
                    stdout_buffer += data
                    decoded_data = data.decode('utf-8', errors='replace').strip()
                    if verbose:
                        print(f"STDOUT: {decoded_data}")
                    
                    # Try to find the PID of the actual Jupyter process
                    if child_pid is None:
                        pid_match = pid_pattern.search(decoded_data)
                        if pid_match:
                            child_pid = int(pid_match.group(1))
                            if verbose:
                                print(f"Found Jupyter Lab child process PID: {child_pid}")
            
            elif stream == process.stderr:
                data = stream.read(1024)
                if data:
                    stderr_buffer += data
                    decoded_data = data.decode('utf-8', errors='replace').strip()
                    if verbose:
                        print(f"STDERR: {decoded_data}")
        
        # Check both buffers for URL pattern
        for buffer_name, buffer_content in [("stdout", stdout_buffer), ("stderr", stderr_buffer)]:
            try:
                # Convert binary buffer to string for regex matching
                buffer_str = buffer_content.decode('utf-8', errors='replace')
                
                # Look for PID in the output if we haven't found it yet
                if child_pid is None:
                    pid_match = pid_pattern.search(buffer_str)
                    if pid_match:
                        child_pid = int(pid_match.group(1))
                        print(f"Found Jupyter Lab child process PID: {child_pid}")
                
                # Look for the URL
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

                    if verbose:
                        print(f"  Base URL: {url_info['base_url']}")
                        print(f"  Port: {url_info['port']}")
                        print(f"  Token: {url_info['token']}")
                    
                    # If we couldn't find the child PID in the output, try to find it through the port
                    if child_pid is None:
                        try:
                            child_pid = find_process_by_port(int(port_number))
                            if child_pid:
                                print(f"Found Jupyter Lab child process PID by port: {child_pid}")
                        except:
                            print("Could not determine child PID by port")
                    
                    return process, url_info, child_pid
            except Exception as e:
                print(f"Error processing {buffer_name} buffer: {e}")
        
        # A small sleep is still needed to prevent CPU spinning
        time.sleep(0.1)
    
    # If we get here, we timed out waiting for the URL
    print("Timeout reached, terminating process...")
    cleanup_processes(process, child_pid)
    
    # Print any accumulated output for debugging
    print("\nLast stdout output:")
    print(stdout_buffer.decode('utf-8', errors='replace'))
    print("\nLast stderr output:")
    print(stderr_buffer.decode('utf-8', errors='replace'))
    
    raise TimeoutError(f"Timed out after {timeout}s waiting for Jupyter Lab URL")

def find_process_by_port(port):
    """Find a process that is listening on the specified port."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return conn.pid
    except:
        pass
    return None

def cleanup_processes(parent_process, child_pid=None):
    """Clean up both the parent process and any child processes."""
    # First try to terminate the child process if we know its PID
    if child_pid:
        try:
            child_process = psutil.Process(child_pid)
            print(f"Terminating child process {child_pid}...")
            child_process.terminate()
            try:
                child_process.wait(timeout=5)
            except psutil.TimeoutExpired:
                print(f"Child process {child_pid} didn't terminate gracefully, killing it")
                child_process.kill()
        except psutil.NoSuchProcess:
            print(f"Child process {child_pid} no longer exists")
        except Exception as e:
            print(f"Error terminating child process: {e}")
    
    # Now try to terminate the parent process
    try:
        if parent_process.poll() is None:  # Check if still running
            print(f"Terminating parent process {parent_process.pid}...")
            parent_process.terminate()
            try:
                parent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Parent process didn't terminate gracefully, killing it")
                parent_process.kill()
    except Exception as e:
        print(f"Error terminating parent process: {e}")