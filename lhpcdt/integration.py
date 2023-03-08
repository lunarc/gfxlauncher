#!/usr/bin/env python

import os, sys

class DesktopMenu:
    def __init__(self):
        self.__menu_location = "~/.config/menus/applications-merged"
        self.__app_location = "~/.local/share/applications"
        self.__dir_location = "~/.local/share/desktop-directories"
        self.__resolve_locations()

        self.__entries = []

        self.__prefix = "lhpcdt_"

    def __resolve_locations(self):
        self.__abs_app_location = os.path.abspath(os.path.expanduser(self.__app_location))
        self.__abs_dir_location = os.path.abspath(os.path.expanduser(self.__dir_location))
        self.__abs_menu_location = os.path.abspath(os.path.expanduser(self.__menu_location))

    def __check_directories(self):
        
        if not 

    def add_entry(self, entry):
        self.__entries.append(entry)

    def print_menus(self):
        for entry in self.__entries:
            print(self.__prefix + entry.filename)
            print(entry)

    def generate(self):
        for entry in self.__entries:
            entry_filename = self.__prefix + entry.filename
            abs_entry_filename = os.path.join(self.abs_app_location, entry_filename)
            with open(abs_entry_filename, "w") as f:
                f.write(str(entry))

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
        return self.__name.lower().replace(" ", "_") + ".desktop"

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



if __name__ == "__main__":

    desktop_entry = DesktopEntry()
    desktop_entry.name = "VS Code 2"
    desktop_entry.exec = "code"
    desktop_entry.categories.append("Accessories")

    desktop_menu = DesktopMenu()
    desktop_menu.add_entry(desktop_entry)
    desktop_menu.generate()
    
