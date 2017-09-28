#!/bin/env python

import os
import sys
import subprocess
import time
from subprocess import Popen, PIPE, STDOUT


class SSH(object):

    def __init__(self):
        self.tty = True
        self.tunnelX11 = True
        self.shell = True
        self.trustedX11 = True
        self.compression = True
        self.process = None
        self.strictHostKeyCheck = False
        self._options = ""
        self._update_options()

    def _update_options(self):
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
        if self.process != None:
            self.process.terminate()

    def is_active(self):
        self.process.poll()
        return self.process.returncode == None

    def execute(self, node, command):
        self._update_options()
        self.process = Popen("ssh %s %s '%s'" %
                             (self._options, node, command), shell=self.shell)
        # return subprocess.call("ssh %s %s '%s'" % (self._options, node,
        # command), shell=self.shell)


class VGLConnect(object):

    def __init__(self):
        self.tty = False
        self.tunnelX11 = False
        self.shell = True
        self.trustedX11 = False
        self.compression = False
        self.process = None
        self.display = ""
        self.vgl_path = "/sw/pkg/rviz/vgl/bin/latest"

        self._options = ""
        self._update_options()

        self.vgl_cmd = ""

    def _update_options(self):
        self._options = ""
        if self.tty:
            self._options += " -t"
        if self.tunnelX11:
            self._options += " -X"
        if self.trustedX11:
            self._options += " -Y"
        if self.compression:
            self._options += " -C"
        if self.display!="":
            self._options += " -display %s" % (self.display)

    def terminate(self):
        if self.process != None:
            self.process.terminate()

    def is_active(self):
        self.process.poll()
        return self.process.returncode == None

    def execute(self, node, command):
        print("VGLConnect.execute:")
        self._update_options()

        if self.vgl_path!="":
            self._vgl_cmd = os.path.join(self.vgl_path, 'vglconnect')

        print("vglconnect %s %s '%s'" % (self._options, node, "vglrun %s" % (command)))
        self.process = Popen("%s %s %s '%s'" %
                             (self._vgl_cmd, self._options, node, "vglrun %s" % (command)), shell=self.shell)

        print("Popen completed")
        # return subprocess.call("vglconnect %s %s '%s'" % (self._options,
        # node, command), shell=self.shell)
