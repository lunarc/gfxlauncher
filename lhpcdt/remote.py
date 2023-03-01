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

"""
Remote launch module

This module implements different classes for remote launch methods.
"""

import os, sys, subprocess, socketserver

from subprocess import Popen, PIPE, STDOUT

def find_available_port():
    """Find an available tcp port."""

    with socketserver.TCPServer(("localhost", 0), None) as s:
        free_port = s.server_address[1]

    return free_port


class SSH(object):
    """Implements a SSH connection"""

    def __init__(self, local_exec=False):
        self.tty = False
        self.tunnelX11 = True
        self.shell = True
        self.trustedX11 = True
        self.compression = True
        self.process = None
        self.strictHostKeyCheck = True
        self.output = ""
        self.error = ""
        self._options = ""
        self._update_options()
        self.local_exec = local_exec

        self.cmd = ""
        self.node = ""
        self.re_execute_count = 0

    def _update_options(self):
        """Update SSH options"""
        self._options = ""
        if self.tty:
            self._options += " -t"
        if self.tunnelX11:
            self._options += " -X"
        if self.trustedX11:
            self._options += " -Y"
        if self.compression:
            self._options += " -C"
        if not self.strictHostKeyCheck:
            self._options += " -oStrictHostKeyChecking=no"

    def terminate(self):
        """Terminate SSH connection process"""
        if not self.local_exec:
            if self.process != None:
                self.process.terminate()

    def is_active(self):
        """Return SSH connection status"""
        self.process.poll()
        return self.process.returncode == None

    def wait(self):
        """Blocking wait for process to finish."""
        self.process.wait()        

    def execute(self, node, command, re_count=0):
        """Execute command on a node/host"""

        self.re_execute_count = re_count

        self._update_options()

        self.node = node
        self.cmd = command

        if not self.local_exec:
            print("ssh %s %s '%s'" % (self._options, node, command))
            self.process = Popen("ssh %s %s '%s'" %
                                 (self._options, node, command), shell=self.shell)
        else:
            self.process = Popen("%s" %
                                 (command), shell=self.shell)

    def execute_again(self):
        """Execute again with the same command and node"""

        if self.process!=None:
            self.terminate()

        self.re_execute_count += 1
            
        self.execute(self.node, self.cmd, re_count=self.re_execute_count)

    def execute_with_output(self, node, command, re_count=0):
        """Execute command node, capturing output."""

        self.re_execute_count = re_count
        self._update_options()

        if not self.local_exec:
            self.process = Popen("ssh %s %s '%s'" %
                                 (self._options, node, command), shell=self.shell, stdout=PIPE)
        else:
            self.process = Popen("%s" %
                                 (command), shell=self.shell, stdout=PIPE)


        output, error = self.process.communicate()
        self.std_output = output
        self.std_error = error

        return output

class SSHForwardTunnel(object):
    def __init__(self, local_port=-1, dest_server="", remote_port=-1, server_hostname=""):
        self.local_port = local_port 
        self.remote_port = remote_port
        self.dest_server = dest_server
        self.server_hostname = server_hostname
        self.strict_host_key_check = False
        self.__options = ""
        self.__process = None

    def __update_options(self):
        """Update SSH options"""

        if self.local_port<0:
            self.local_port = find_available_port()

        self.__options = "-N -L %d:%s:%d %s" % (self.local_port, self.dest_server, self.remote_port, self.server_hostname)
        if not self.strict_host_key_check:
            self.__options += " -oStrictHostKeyChecking=no"

    def terminate(self):
        """Terminate SSH connection process"""
        if self.__process != None:
            self.__process.terminate()

    def is_active(self):
        """Return SSH connection status"""
        self.__process.poll()
        return self.__process.returncode == None

    def wait(self):
        self.__process.wait()        

    def execute(self):
        self.__update_options()
        print("Tunnel cmdline: %s" % ("ssh %s" % (self.__options)))
        self.__process = Popen("ssh %s" % (self.__options), shell=True)
    

class VGLConnect(object):
    """Implements a remote connecting supporting VirtualGL"""

    def __init__(self):
        """Initialise class property defaults"""
        self.tty = False
        self.tunnelX11 = False
        self.shell = True
        self.trustedX11 = False
        self.compression = False
        self.process = None
        self.display = ""
        self.vglrun = True
        self.vgl_path = "/sw/pkg/rviz/vgl/bin/latest"
        self.secure = False

        self._options = ""
        self._update_options()

        self.vgl_cmd = ""

        self.cmd = ""
        self.node = ""
        self.re_execute_count = 0

    def _update_options(self):
        """Update command line options"""
        self._options = ""
        if self.tty:
            self._options += " -t"
        if self.secure:
            self._options += " -s"
        if self.tunnelX11:
            self._options += " -X"
        if self.trustedX11:
            self._options += " -Y"
        if self.compression:
            self._options += " -C"
        if self.display != "":
            self._options += " -display %s" % (self.display)

    def terminate(self):
        """Terminate connection process"""

        if self.process != None:
            self.process.terminate()

    def is_active(self):
        """Return status of VGL connection"""

        self.process.poll()
        return self.process.returncode == None

    def wait(self):
        """Wait for process to finish."""

        self.process.wait()

    def execute_again(self):
        """Execute command again with same parameters."""

        self.re_execute_count += 1

        if self.process!=None:
            self.terminate()

        self.execute(self.node, self.cmd, re_count=self.re_execute_count)

    def execute(self, node, command, re_count=0):
        """Execute a command on a host"""

        self.node = node
        self.cmd = command
        self.re_execute_count = re_count

        self._update_options()

        if self.vgl_path != "":
            self._vgl_cmd = os.path.join(self.vgl_path, 'vglconnect')

        if self.vglrun:
            #print("vglconnect %s %s '%s'" % (self._options, node, "vglrun %s" % (command)))
            self.process = Popen("%s %s %s '%s'" %
                                (self._vgl_cmd, self._options, node, "vglrun %s" % (command)), shell=self.shell)
        else:
            #print("vglconnect %s %s '%s'" % (self._options, node, command))
            self.process = Popen("%s %s %s '%s'" %
                                (self._vgl_cmd, self._options, node, command), shell=self.shell)

class StatusProbe(SSH):
    def __init__(self, local_exec=False):
        super(StatusProbe, self).__init__(local_exec)
        self.total_mem = -1
        self.free_mem = -1
        self.used_mem = -1
        self.memory_unit = "G" 
        self.cpu_usage = -1
        self.cpu_unit = "%"

    def print_summary(self):
        """Print probe summary"""

        print("Total memory  : "+str(self.total_mem)+self.memory_unit)
        print("Used memory   : "+str(self.used_mem)+self.memory_unit)
        print("CPU usage     : "+str(self.cpu_usage)+self.cpu_unit)

    def check_memory(self, node):
        """Check memory status of node"""

        """
                      total        used        free      shared  buff/cache   available
        Mem:             94           1          91           0           1          92
        Swap:             7           0           7
        """

        output = self.execute_with_output(node, "free -g").decode('ascii')
        lines = output.split("\n")
        mem_items = lines[1].split()

        self.total_mem = int(mem_items[1])
        self.free_mem = int(mem_items[3])
        self.used_mem = self.total_mem - self.free_mem

    def check_cpu_usage(self, node):
        """Check cpu usage of node"""

        """
        vmstat -w
        procs -----------------------memory---------------------- ---swap-- -----io---- -system-- --------cpu--------
         r  b         swpd         free         buff        cache   si   so    bi    bo   in   cs  us  sy  id  wa  st
         1  0     12958956      2536352          272     27033172    0    0     2     1    0    0   2   5  92   0   0
        """

        output = self.execute_with_output(node, "vmstat -w").decode('ascii')
        lines = output.split("\n")
        vmstat_items = lines[2].split()

        self.cpu_usage = int(vmstat_items[12]) + int(vmstat_items[13])

    def check_gpu_usage(self, node):
        pass

        """
        ==============NVSMI LOG==============
        
        Timestamp                           : Fri Jun  8 15:59:16 2018
        Driver Version                      : 390.12
        
        Attached GPUs                       : 4
        GPU 00000000:0A:00.0
            Utilization
                Gpu                         : 0 %
                Memory                      : 0 %
                Encoder                     : 0 %
                Decoder                     : 0 %
            GPU Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            Memory Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            ENC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            DEC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
        
        GPU 00000000:0D:00.0
            Utilization
                Gpu                         : 0 %
                Memory                      : 0 %
                Encoder                     : 0 %
                Decoder                     : 0 %
            GPU Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            Memory Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            ENC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            DEC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
        
        GPU 00000000:2B:00.0
            Utilization
                Gpu                         : 0 %
                Memory                      : 0 %
                Encoder                     : 0 %
                Decoder                     : 0 %
            GPU Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            Memory Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            ENC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            DEC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
        
        GPU 00000000:30:00.0
            Utilization
                Gpu                         : 0 %
                Memory                      : 0 %
                Encoder                     : 0 %
                Decoder                     : 0 %
            GPU Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            Memory Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            ENC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
            DEC Utilization Samples
                Duration                    : 18446744073709.21 sec
                Number of Samples           : 99
                Max                         : 0 %
                Min                         : 0 %
                Avg                         : 0 %
        """

        output = self.execute_with_output(node, "nvidia-smi -q  -d UTILIZATION").decode('ascii')
        lines = output.split("\n")

        self.gpu_usage = []

        for line in lines:
            if line.find("Gpu")!=-1:
                usage = int(line.split(":")[1].split("%")[0])
                self.gpu_usage.append(usage)

    def check_all(self, node):
        self.check_cpu_usage(node)
        self.check_memory(node)
        self.check_gpu_usage(node)

class XFreeRDP(object):
    """Implements a RDP connection"""

    def __init__(self, hostname):
        self.hostname = hostname
        self.process = None
        self.output = ""
        self.error = ""
        self.__xfreerdp_path = "/sw/pkg/freerdp/2.0.0-rc4/bin"
        self.__xfreerdp_cmd = "xfreerdp"
        self.__update_path()

    def __update_path(self):
        self.xfreerdp_binary = os.path.join(self.xfreerdp_path, self.xfreerdp_cmd)

    def terminate(self):
        """Terminate RDP connection process"""
        if self.process != None:
            self.process.terminate()

    def is_active(self):
        """Return RDP connection status"""
        self.process.poll()
        return self.process.returncode == None

    def wait(self):
        """Wait for the process to exit"""
        self.process.wait()        

    def execute(self):
        """Execute command on a node/host"""
        #self._update_options()

        #cmd_line = 'xfreerdp -u $(zenity --entry --title="%s" --text="Enter your username") -p $(zenity --entry --title="Password" --text="Enter your _password:" --hide-text) --ignore-certificate %s'

        #cmd_line = 'xfreerdp --ignore-certificate %s'
        #cmd_line = '/sw/pkg/freerdp/2.0.0-rc4/bin/xfreerdp /v:%s /u:$USER /d:ad.lunarc /sec:tls -themes -wallpaper /size:1280x1024 /dynamic-resolution /cert-ignore'

        #cmd_line = '%s /v:%s /u:$USER /d:ad.lunarc /sec:tls /cert-tofu /cert-ignore /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard -themes -wallpaper /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"'

        cmd_line = '%s /v:%s /u:$USER /d:ad.lunarc /sec:tls /cert-ignore /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"'

        #cmd_line = '/sw/pkg/freerdp/2.0.0-rc4/bin/xfreerdp /v:%s /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard -themes -wallpaper /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"'
        self.process = Popen(cmd_line % (self.xfreerdp_binary, self.hostname), shell=True)

    def execute_with_output(self, node, command):
        self.process = Popen("ssh %s %s '%s'" %
                             (self._options, node, command), shell=self.shell, stdout=PIPE)

        output, error = self.process.communicate()

        return output

    def set_xfreerdp_path(self, p):
        """Set method for xfreerdp_path property"""
        self.__xfreerdp_path = p
        self.__update_path()

    def get_xfreerdp_path(self):
        """Get method for xfreerdp_path property"""
        return self.__xfreerdp_path

    def set_xfreerdp_cmd(self, c):
        """Set method for xfreerdp_cmd property"""
        self.__xfreerdp_cmd = c
        self.__update_path()
    
    def get_xfreerdp_cmd(self):
        """Get method for xfreerdp_cmd property"""
        return self.__xfreerdp_cmd

    xfreerdp_path = property(get_xfreerdp_path, set_xfreerdp_path)
    xfreerdp_cmd = property(get_xfreerdp_cmd, set_xfreerdp_cmd)


if __name__ == "__main__":

    print("Finding a free port...")

    port = find_available_port()

    print("Found", port)

    #ssh_tunnel = SSHForwardTunnel(8889,"au322",8888,"au322")
    #ssh_tunnel.execute()

    #while ssh_tunnel.is_active():
    #    print("Tunnel is running...")
    #    time.sleep(3)



