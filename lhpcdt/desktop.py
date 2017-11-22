#!/bin/env python

# --- Classes

class Menu:
    """XDG Menu class"""

    def __init__(self):
        """Constructor"""
        self.name = "Lunarc On-Demand"
        self.dir_file = "Lunarc-On-Demand.directory"
        self.items = []
        self.dest_filename = ""
        self._indent_level = 0
        self._tab = "    "

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

    def write(self):
        """Write menu XML"""
        if self.dest_filename == "":
            return

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
        self._end_tag(f, "Menu")
        self._end_tag(f, "Menu")

        f.close()


class DesktopEntry:
    """Implements a XDG menu entry"""

    def __init__(self):
        self._version = "1.0"
        self._type = "Application"
        self.terminal = False
        self.icon = ""
        self.name = "Entry"
        self.exec_file = ""
        self.filename = ""

    def write(self):
        """Write desktop entry"""
        if self.filename == "":
            return

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

        f.close()
