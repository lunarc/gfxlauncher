#!/bin/env python

import sys, os
#from typing_extensions import final

# --- Classes

class Menu:
    """XDG Menu class"""

    def __init__(self, dryrun = False):
        """Constructor"""
        self.name = "Lunarc Applications On-Demand"
        self.dir_file = "Lunarc-On-Demand.directory"
        self.items = []
        self.sub_menus = {}
        self.dest_filename = ""
        self.directory_dir = ""
        self._indent_level = 0
        self._tab = "    "
        self.dryrun = dryrun

    def _write_header(self, f):
        """Writes menu header"""
        f.write('<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"\n')
        f.write('  "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">\n')

    def _indent(self):
        """Increase indentation level"""
        self._indent_level += 1

    def _dedent(self):
        """Decrease indentation level"""
        if self._indent_level > 0:
            self._indent_level -= 1

    def _tag_value(self, f, name, value):
        """Write a single line tag value"""
        f.write(self._tab * self._indent_level + "<%s>%s</%s>\n" % (name, value, name))

    def _tag(self, f, name):
        """Begin a tag"""
        f.write(self._tab * self._indent_level + "<%s>\n" % (name))

    def _close_tag(self, f, name):
        """End a tag"""
        f.write(self._tab * self._indent_level + "</%s>\n" % (name))

    def _begin_tag(self, f, name):
        """Begin a tag and increas indent"""
        self._tag(f, name)
        self._indent()

    def _end_tag(self, f, name):
        """End a tag and decreas indentation"""
        self._dedent()
        self._close_tag(f, name)

    def _write_dir_entry(self, filename, name):
        """Write directory entry"""

        try:

            f = None

            if self.dryrun:
                f = sys.stdout
                f.write("direntry = "+filename+"\n")
            else:
                f = open(filename, "w")

            f.write("[Desktop Entry]\n")
            f.write("Type = Directory\n")
            f.write("Name = %s\n" % name)
            f.write("Icon = /usr/share/icons/mate/48x48/actions/lunarc.png\n")

        except PermissionError:
            print("Menu: Couldn't write, %s, check permissions." % filename)
        finally:
            if not self.dryrun:
                if f!=None:
                    f.close()

            # [Desktop Entry]
            # Type = Directory
            # Name = Python
            # Icon = / usr / share / icons / mate / 48
            # x48 / actions / lunarc.png

    def write(self):
        """Write menu XML"""
        if self.dest_filename == "":
            return

        try:

            f = None
            dir_entries = None

            if self.dryrun:
                f = sys.stdout
            else:
                f = open(self.dest_filename, "w")

            self._write_header(f)

            self._begin_tag(f, "Menu")
            self._tag_value(f, "Name", "Applications")
            self._begin_tag(f, "Menu")
            self._tag_value(f, "Name", self.name)
            self._tag_value(f, "Directory", self.dir_file)
            self._begin_tag(f, "Include")

            for item in self.items:
                self._tag_value(f, "Filename", item)

            self._end_tag(f, "Include")

            dir_entries = []

            for key in list(self.sub_menus.keys()):
                self._begin_tag(f, "Menu")
                self._tag_value(f, "Name", key)
                self._tag_value(f, "Directory", key.replace(" ", "_")+".directory")
                dir_entries.append([key, key.replace(" ", "_")+".directory"])
                self._begin_tag(f, "Include")
                for item in self.sub_menus[key]:
                    self._tag_value(f, "Filename", item)
                self._end_tag(f, "Include")
                self._end_tag(f, "Menu")

            self._end_tag(f, "Menu")
            self._end_tag(f, "Menu")

            #< Menu >
            #< Name > Python < / Name >
            #< Directory > Python.directory < / Directory >
            #< Include >
            #< Filename > Paraview.desktop < / Filename >
            #< / Include >
            #< / Menu >

        except PermissionError:
            print("Menu: Couldn't write, %s, check permissions" % self.dest_filename)
            return
        finally:
            if not self.dryrun:
                if f!=None:
                    f.close()

        for dir_entry in dir_entries:
            filename = os.path.join(self.directory_dir, dir_entry[1])
            self._write_dir_entry(filename, dir_entry[0])

class DesktopEntry:
    """Implements a XDG menu entry"""

    def __init__(self, dryrun):
        self._version = "1.0"
        self._type = "Application"
        self.terminal = False
        self.icon = ""
        self.name = "Entry"
        self.exec_file = ""
        self.filename = ""
        self.dryrun = dryrun

    def write(self):
        """Write desktop entry"""
        if self.filename == "":
            return

        try:

            f = None

            if self.dryrun:
                f = sys.stdout
                f.write("desktop entry = "+self.filename+"\n")
            else:
                f = open(self.filename, "w")

            f.write("[Desktop Entry]\n")
            f.write("Name=%s\n" % self.name)
            f.write("Type=%s\n" % self._type)
            if self.terminal:
                f.write("Terminal=true\n")
            else:
                f.write("Terminal=false\n")

            if self.icon != "":
                f.write("Icon=%s\n" % self.icon)

            if self.exec_file != "":
                f.write("Exec=%s\n" % self.exec_file)

            if not self.dryrun:
                f.close()

        except PermissionError:
            print("DesktopEntry: Couldn't write, %s, check permissions. " % self.filename)
        finally:
            if not self.dryrun:
                if f!=None:
                    f.close()
