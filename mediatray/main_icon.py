import os

import rox

import gtk

from traylib import *
from traylib.menu_icon import MenuIcon

from mediatray.host_editor import HostEditor


ICON_THEME.append_search_path(os.path.join(rox.app_dir, 'icons'))


class MainIcon(MenuIcon):

    def __init__(self, tray, icon_config, tray_config, win_config,
                 host_manager):
        MenuIcon.__init__(self, tray, icon_config, tray_config)
        win_config.add_configurable(self)
        self.__host_manager = host_manager

    def update_option_all_workspaces(self):
        self.update_tooltip()

    def click(self, time):
        pass

    def mouse_wheel_up(self, time):
        self.tray.win_config.all_workspaces = True

    def mouse_wheel_down(self, time):
        self.tray.win_config.all_workspaces = False

    def get_icon_names(self):
        return ['computer']

    def get_custom_menu_items(self):
        menu_item = gtk.ImageMenuItem(gtk.STOCK_ADD)
        menu_item.set_label(_("Add Host"))
        menu_item.connect("activate", self.__add_host)
        return [menu_item]

    def __add_host(self, menu_item):
        dialog = HostEditor(self.__host_manager)
        dialog.show()

    def make_tooltip(self):
        if self.tray.win_config.all_workspaces:
            s = _("Scroll down to only show windows of this workspace.")
        else:
            s = _("Scroll up to show windows of all workspaces.")
        return s
