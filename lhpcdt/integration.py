#!/usr/bin/env python

import os, sys

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
        self.__indent_level = 0
        self.__tab = "    "
        self.dryrun = dryrun
        self.entry_prefix = "lhpcdt_"

    def __write_header(self, f):
        """Writes menu header"""
        f.write('<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"\n')
        f.write('  "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">\n')

    def __indent(self):
        """Increase indentation level"""
        self.__indent_level += 1

    def __dedent(self):
        """Decrease indentation level"""
        if self.__indent_level > 0:
            self.__indent_level -= 1

    def __tag_value(self, f, name, value, attr="", attr_value=""):
        """Write a single line tag value"""
        if attr=="":
            f.write(self.__tab * self.__indent_level + "<%s>%s</%s>\n" % (name, value, name))
        else:
            f.write(self.__tab * self.__indent_level + '<%s %s="%s">%s</%s>\n' % (name, attr, attr_value, value, name))

    def __tag(self, f, name, attr="", attr_value=""):
        """Begin a tag"""
        if attr == "":
            f.write(self.__tab * self.__indent_level + "<%s>\n" % (name))
        else:
            f.write(self.__tab * self.__indent_level + '<%s %s="%s">\n' % (name, attr, attr_value))

    def __close_tag(self, f, name):
        """End a tag"""
        f.write(self.__tab * self.__indent_level + "</%s>\n" % (name))

    def __begin_tag(self, f, name, attr="", attr_value=""):
        """Begin a tag and increas indent"""
        self.__tag(f, name, attr, attr_value)
        self.__indent()

    def __end_tag(self, f, name):
        """End a tag and decreas indentation"""
        self.__dedent()
        self.__close_tag(f, name)

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

            self.__write_header(f)

            self.__begin_tag(f, "Menu")
            self.__tag_value(f, "Name", "Applications")
            self.__tag_value(f, "MergeFile", value="/etc/xdg/menus/applications.menu", attr="type", attr_value="parent")
            self.__begin_tag(f, "Menu")
            self.__tag_value(f, "Name", self.name)
            self.__tag_value(f, "Directory", self.dir_file)
            self.__begin_tag(f, "Include")

            for item in self.items:
                self.__tag_value(f, "Filename", self.entry_prefix + item.filename)

            self.__end_tag(f, "Include")

            dir_entries = []

            for key in list(self.sub_menus.keys()):
                self.__begin_tag(f, "Menu")
                self.__tag_value(f, "Name", key)
                self.__tag_value(f, "Directory", key.replace(" ", "_")+".directory")
                dir_entries.append([key, key.replace(" ", "_")+".directory"])
                self.__begin_tag(f, "Include")
                for item in self.sub_menus[key]:
                    self.__tag_value(f, "Filename", item)
                self.__end_tag(f, "Include")
                self.__end_tag(f, "Menu")

            self.__end_tag(f, "Menu")
            self.__end_tag(f, "Menu")

        except PermissionError:
            print("Menu: Couldn't write, %s, check permissions" % self.dest_filename)
            return
        finally:
            if not self.dryrun:
                if f!=None:
                    f.close()

        #for dir_entry in dir_entries:
        #    filename = os.path.join(self.directory_dir, dir_entry[1])
        #    self.__write_dir_entry(filename, dir_entry[0])


class DesktopMenu:
    def __init__(self):

        self.__name = "My Menu"
        self.__menu_location = "~/.config/menus/applications-merged"
        self.__app_location = "~/.local/share/applications"
        self.__dir_location = "~/.local/share/desktop-directories"
        self.__resolve_locations()
        self.__check_directories()

        self.__entries = []
        self.__dir_entry = DirectoryEntry()

        self.__prefix = "lhpcdt_"

        self.__menu_filename = ""
        self.__dir_filename = ""

        self.__menu = Menu()
        self.__menu.name = self.__name

        self.__update_filenames()

    def __resolve_locations(self):
        self.__abs_app_location = os.path.abspath(os.path.expanduser(self.__app_location))
        self.__abs_dir_location = os.path.abspath(os.path.expanduser(self.__dir_location))
        self.__abs_menu_location = os.path.abspath(os.path.expanduser(self.__menu_location))

    def __check_directories(self):
        if not os.path.exists(self.abs_app_location):
            os.makedirs(self.abs_app_location)
        if not os.path.exists(self.abs_dir_location):
            os.makedirs(self.abs_dir_location)
        if not os.path.exists(self.abs_menu_location):
            os.makedirs(self.abs_menu_location)

    def __update_filenames(self):
        self.__menu_filename = self.__name.lower().replace(" ", "_") + ".menu"
        self.__dir_filename = self.__name.lower().replace(" ", "_") + ".directory"
        self.__menu.dest_filename = os.path.join(self.__abs_menu_location, "applications.menu")

    def __update(self):
        self.__resolve_locations()
        self.__check_directories()
        self.__update_filenames()
        self.__dir_entry.name = self.name


    def add_entry(self, entry):
        self.__entries.append(entry)

    def add_dir(self, dir_entry):
        self.__dirs.append(dir_entry)

    def print_menus(self):
        for entry in self.__entries:
            print(self.__prefix + entry.filename)
            print(entry)

    def generate(self):
        self.__update()

        # Write desktop entries

        for entry in self.__entries:
            entry_filename = self.__prefix + entry.filename
            abs_entry_filename = os.path.join(self.abs_app_location, entry_filename)
            with open(abs_entry_filename, "w") as f:
                f.write(str(entry))

        # Write menu file

        self.__menu.items = self.__entries
        self.__menu.name = self.__name
        self.__menu.dir_file = self.__dir_filename
        self.__menu.entry_prefix = self.__prefix
        self.__menu.write()

        # Write directory file

        abs_dir_filename = os.path.join(self.abs_dir_location, self.__dir_filename) 

        with open(abs_dir_filename, "w") as f:
            f.write(str(self.__dir_entry))


        

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value
        self.__update_filenames()

    @property
    def app_location(self):
        return self.__app_location

    @app_location.setter
    def location(self, value):
        self.__app_location = value
        self.__resolve_location()

    @property
    def dir_location(self):
        return self.__dir_location

    @dir_location.setter
    def dir_location(self, value):
        self.__dir_location = value
        self.__resolve_locations()

    @property
    def abs_app_location(self):
        self.__resolve_locations()
        return self.__abs_app_location

    @property
    def app_location(self):
        return self.__app_location

    @property
    def abs_dir_location(self):
        self.__resolve_locations()
        return self.__abs_dir_location

    @property
    def abs_menu_location(self):
        self.__resolve_locations()
        return self.__abs_menu_location

    @dir_location.setter
    def dir_location(self, value):
        self.__dir_location = value
        self.__resolve_locations()

    


    

class DesktopEntry:
    def __init__(self):
        self.__type = "Application"
        self.__encoding = "UTF-8"
        self.__name = "NoName"
        self.__comment = "NoName comment"
        self.__icon = "system-icon"
        self.__exec = ""
        self.__terminal = False
        self.__categories = []
        self.__extension = ".desktop"

        self.__out_string = ""

    def __clear(self):
        self.__out_string = ""

    def __add_line(self, str):
        self.__out_string += str + "\n"

    def __generate(self):
        self.__clear()
        self.__add_line("[Desktop Entry]")
        if (self.__type!=""):
            self.__add_line(f"Type={self.__type}")
        if (self.__encoding!=""):
            self.__add_line(f"Encoding={self.__encoding}")
        if (self.__name!=""):
            self.__add_line(f"Name={self.__name}")
        if (self.__comment!=""):
            self.__add_line(f"Comment={self.__comment}")
        if (self.__icon!=""):
            self.__add_line(f"Icon={self.__icon}")
        if (self.__exec!=""):
            self.__add_line(f"Exec={self.__exec}")
        if self.terminal:
            self.__add_line(f"Terminal=true")
        else:
            self.__add_line(f"Terminal=false")
        
        categories_string = ";".join(self.__categories)
        if (categories_string!=""):
            self.__add_line(f"Categories={categories_string}")

    @property
    def filename(self):
        return self.__name.lower().replace(" ", "_") + self.__extension

    @property
    def extension(self):
        return self.__extension

    @extension.setter
    def extension(self, value):
        self.__extension = value

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value):
        self.__type = value

    @property
    def encoding(self):
        return self.__encoding

    @encoding.setter
    def encoding(self, value):
        self.__encoding = value

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value
    
    @property
    def comment(self):
        return self.__comment

    @comment.setter
    def comment(self, value):
        self.__comment = value
    
    @property
    def icon(self):
        return self.__icon

    @icon.setter
    def icon(self, value):
        self.__icon = value

    @property
    def exec(self):
        return self.__exec

    @exec.setter
    def exec(self, value):
        self.__exec = value

    @property
    def terminal(self):
        return self.__terminal

    @terminal.setter
    def terminal(self, value):
        self.__terminal = value

    @property
    def categories(self):
        return self.__categories

    @property
    def out_string(self):
        self.__generate()
        return self.__out_string

    def __str__(self):
        return self.out_string

class DirectoryEntry(DesktopEntry):
    def __init__(self):
        super().__init__()
        self.extension = ".directory"
        self.type = "Directory"
        self.comment = "My directory"
        self.name = "My directory"
        

if __name__ == "__main__":

    desktop_entry = DesktopEntry()
    desktop_entry.name = "VS Code 2"
    desktop_entry.exec = "code"
    desktop_entry.categories.append("Accessories")

    desktop_menu = DesktopMenu()
    desktop_menu.name = "LUNARC Applications"
    desktop_menu.add_entry(desktop_entry)
    desktop_menu.generate()
    
    desktop_menu = DesktopMenu()
    desktop_menu.name = "LUNARC On-Demand Applications"
    desktop_menu.add_entry(desktop_entry)
    desktop_menu.generate()
