#!/usr/bin/env python

import os, sys, time, logging

from lhpcdt import config

class XmlBase:
    def __init__(self):
        self.__indent_level = 0
        self.__tab = "    "

    def write_header(self, f):
        """Writes menu header"""
        f.write('<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"\n')
        f.write('  "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">\n')

    def indent(self):
        """Increase indentation level"""
        self.__indent_level += 1

    def dedent(self):
        """Decrease indentation level"""
        if self.__indent_level > 0:
            self.__indent_level -= 1

    def tag_value(self, f, name, value, attr="", attr_value=""):
        """Write a single line tag value"""
        if attr=="":
            f.write(self.__tab * self.__indent_level + "<%s>%s</%s>\n" % (name, value, name))
        else:
            f.write(self.__tab * self.__indent_level + '<%s %s="%s">%s</%s>\n' % (name, attr, attr_value, value, name))

    def tag(self, f, name, attr="", attr_value=""):
        """Begin a tag"""
        if attr == "":
            f.write(self.__tab * self.__indent_level + "<%s>\n" % (name))
        else:
            f.write(self.__tab * self.__indent_level + '<%s %s="%s">\n' % (name, attr, attr_value))

    def close_tag(self, f, name):
        """End a tag"""
        f.write(self.__tab * self.__indent_level + "</%s>\n" % (name))

    def begin_tag(self, f, name, attr="", attr_value=""):
        """Begin a tag and increas indent"""
        self.tag(f, name, attr, attr_value)
        self.indent()

    def end_tag(self, f, name):
        """End a tag and decreas indentation"""
        self.dedent()
        self.close_tag(f, name)

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
        return self.__name.lower().replace("/", "_").replace(" ", "_") + self.__extension

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



class UserMenus(XmlBase):
    def __init__(self, dryrun=False):
        super().__init__()
        self.__menus = []

        # Default locations

        cfg = config.GfxConfig.create()

        self.__menu_location = cfg.menu_location
        self.__app_location = cfg.app_location
        self.__dir_location = cfg.dir_location
        self.__ondemand_location = cfg.ondemand_location
        self.__force_refresh = False

        # self.__menu_location = "~/.config/menus/applications-merged"
        # self.__app_location = "~/.local/share/applications"
        # self.__dir_location = "~/.local/share/desktop-directories"
        # self.__ondemand_location = "~/.local/share/ondemand-dt"

        self.__menu_filename = ""

        self.__name = "On-Demand applications"

        self.__desktop_prefixes = ['gnome', 'mate', 'kde']

        self.__dryrun = dryrun
        self.__use_top_level_menu = False

        self.__menu_name_prefix = "On-Demand "
        self.__desktop_entry_prefix = "gfx-"
        self.__menu_name_no_launch_suffix = " [Desktop]"

        self.__resolve_locations()
        self.__check_directories()
        self.__create_links()

        if os.path.exists(self.time_stamp_filename):
            with open(self.time_stamp_filename, "r") as f:
                line = f.readline()
                value = 0.0
                try:
                    value = float(line)
                except ValueError:
                    value = 0.0

                self.__last_run = value
        else:
            self.__last_run = 0.0


    def __resolve_locations(self):
        self.__abs_app_location = os.path.abspath(os.path.expanduser(self.__app_location))
        self.__abs_dir_location = os.path.abspath(os.path.expanduser(self.__dir_location))
        self.__abs_menu_location = os.path.abspath(os.path.expanduser(self.__menu_location))
        self.__abs_ondemand_location = os.path.abspath(os.path.expanduser(self.__ondemand_location))

    def __check_directories(self):
        logging.debug("Checking directories")
        if not os.path.exists(self.abs_app_location):
            os.makedirs(self.abs_app_location)
        if not os.path.exists(self.abs_dir_location):
            os.makedirs(self.abs_dir_location)
        if not os.path.exists(self.abs_menu_location):
            os.makedirs(self.abs_menu_location)
        if not os.path.exists(self.abs_ondemand_location):
            os.makedirs(self.abs_ondemand_location)

    def __create_links(self):
        logging.debug("Creating links")
        for prefix in self.__desktop_prefixes:
            link_path = self.abs_menu_location.replace("applications-merged", prefix+"-applications-merged")
            if not os.path.exists(link_path):
                os.symlink(self.abs_menu_location, link_path)
                        
    def __update_filenames(self):
        logging.debug("Updating filenames")
        self.__menu_filename = os.path.join(self.__abs_menu_location, "applications.menu")

    def __update(self):
        logging.debug("Updating")
        self.__resolve_locations()
        self.__check_directories()
        self.__update_filenames()

    def add_menu(self, menu):
        logging.debug(f"Adding menu {menu.name}")
        self.__menus.append(menu)

    def add_scripts(self, script_db):
        self.__script_db = script_db

        for category, scripts in script_db.items():

            logging.debug(f"Adding category {category}")

            menu = Menu(self)
            menu.name = category
         
            for script in scripts:
                logging.debug(f"Adding script {script.variables['title']}")
                logging.debug(f"\t cmd = {script.launch_cmd}")
                desktop_entry = DesktopEntry()
                if script.no_launcher:
                    desktop_entry.name = script.variables["title"] + self.__menu_name_no_launch_suffix
                else:
                    desktop_entry.name = script.variables["title"]
                desktop_entry.exec = script.launch_cmd
                desktop_entry.changed = script.changed
                if "icon" in script.variables:
                    desktop_entry.icon = script.variables["icon"]
                menu.add_entry(desktop_entry)

            self.add_menu(menu)

    def generate(self):

        self.__update()

        if self.__menu_filename == "":
            print("menu filename empty")
            return

        dir_entries = None

        with open(self.__menu_filename, "w") as f: 

            logging.debug(f"Writing menu file {self.__menu_filename}")

            self.write_header(f)

            self.begin_tag(f, "Menu")
            self.tag_value(f, "Name", "Applications")
            self.tag_value(f, "MergeFile", value="/etc/xdg/menus/applications.menu", attr="type", attr_value="parent")


            dirs = []

            if self.__use_top_level_menu:

                root_dir_filename = self.__name.replace(" ", "_").lower()+".directory"
                abs_root_dir_filename = os.path.join(self.__abs_dir_location, root_dir_filename)

                root_dir_entry = DirectoryEntry()
                root_dir_entry.name = self.__name

                dirs.append((root_dir_entry, abs_root_dir_filename))

                self.begin_tag(f, "Menu")
                self.tag_value(f, "Name", self.__name)
                self.tag_value(f, "Directory", root_dir_filename)

            for menu in self.__menus:

                menu.prefix = self.__desktop_entry_prefix
                menu.last_run = self.__last_run
                menu.generate()

                dir_filename = menu.name.replace(" ", "_").lower()+".directory"
                abs_dir_filename = os.path.join(self.__abs_dir_location, dir_filename)

                dir_entry = DirectoryEntry()
                dir_entry.name = self.__menu_name_prefix + menu.name

                dirs.append((dir_entry, abs_dir_filename))

                self.begin_tag(f, "Menu")
                self.tag_value(f, "Name", self.__menu_name_prefix + menu.name)
                self.tag_value(f, "Directory", dir_filename)
                self.begin_tag(f, "Include")

                for item in menu.entries:
                    self.tag_value(f, "Filename", menu.prefix + item.filename)

                self.end_tag(f, "Include")
                self.end_tag(f, "Menu")

            dir_entries = []

            self.end_tag(f, "Menu")

            if self.__use_top_level_menu:
                self.end_tag(f, "Menu")

            for dir_entry, abs_filename in dirs:
                with open(abs_filename, "w") as fde:
                    fde.write(str(dir_entry))

        logging.debug(f"Updating timestamp {self.time_stamp_filename}")
        with open(self.time_stamp_filename, "w") as f:
            f.write(str(time.time()))


    @property
    def time_stamp_filename(self):
        return os.path.join(self.abs_ondemand_location, "ondemand-dt.timestamp")

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
    def ondemand_location(self):
        return self.__ondemand_location
    
    @property
    def abs_ondemand_location(self):
        return self.__abs_ondemand_location

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

    @property
    def menu_name_prefix(self):
        return self.__menu_name_prefix
    
    @menu_name_prefix.setter
    def menu_name_prefix(self, value):
        self.__menu_name_prefix = value

    @property
    def desktop_entry_prefix(self):
        return self.__desktop_entry_prefix
    
    @desktop_entry_prefix.setter
    def desktop_entry_prefix(self, value):
        self.__desktop_entry_prefix = value

    @property
    def menu_name_no_launch_suffix(self):
        return self.__menu_name_no_launch_suffix
    
    @menu_name_no_launch_suffix.setter
    def menu_name_no_launch_suffix(self, value):
        self.__menu_name_no_launch_suffix = value

    @property
    def force_refresh(self):
        return self.__force_refresh
    
    @force_refresh.setter
    def force_refresh(self, value):
        self.__force_refresh = value
        
class Menu:
    def __init__(self, parent):

        self.__parent = parent
        self.__name = "My Menu"
        self.__entries = []
        self.__prefix = "lhpcdt_"
        self.__filename = ""
        self.__abs_filename = ""
        self.__force_refresh = False

        self.__last_run = 0.0

    def __update_filenames(self):
        self.__filename = self.prefix + self.__name.lower().replace(" ", "_") + ".directory"
        self.__abs_filename = os.path.join(self.__parent.abs_dir_location, self.__filename)

    def add_entry(self, entry):
        self.__entries.append(entry)

    def add_dir(self, dir_entry):
        self.__dirs.append(dir_entry)

    def print_menus(self):
        for entry in self.__entries:
            print(self.__prefix + entry.filename)
            print(entry)

    def __update(self):
        self.__update_filenames()


    def generate(self):

        self.__update()

        # Write desktop entries

        for entry in self.__entries:

            entry_filename = self.__prefix + entry.filename
            abs_entry_filename = os.path.join(self.__parent.abs_app_location, entry_filename)

            # Only create a new desktop entry if the script has changed.

            if not os.path.exists(abs_entry_filename) or (entry.changed > self.last_run) or self.force_refresh:
                with open(abs_entry_filename, "w") as f:
                    f.write(str(entry))

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value
        self.__update_filenames()

    @property
    def entries(self):
        return self.__entries
    
    @property
    def prefix(self):
        return self.__prefix
    
    @prefix.setter
    def prefix(self, value):
        self.__prefix = value

    @property
    def last_run(self):
        return self.__last_run
    
    @last_run.setter
    def last_run(self, value):
        self.__last_run = value

    @property
    def force_refresh(self):
        return self.__force_refresh
    
    @force_refresh.setter
    def force_refresh(self, value):
        self.__force_refresh = value
    

    

        

if __name__ == "__main__":

    desktop_entry = DesktopEntry()
    desktop_entry.name = "VS Code 2"
    desktop_entry.exec = "code"
    desktop_entry.categories.append("Accessories")

    user_menu = UserMenus()

    menu = Menu(user_menu)
    menu.name = "On-demand applications"
    menu.add_entry(desktop_entry)

    user_menu.add_menu(menu)

    menu = Menu(user_menu)
    menu.name = "On-demand applications 2"
    menu.add_entry(desktop_entry)

    user_menu.add_menu(menu)

    user_menu.generate()


