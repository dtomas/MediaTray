import os

import rox

import gtk

from traylib import *
from traylib.menu_icon import MenuIcon

from mediatray.host_editor import HostEditor


ICON_THEME.append_search_path(os.path.join(rox.app_dir, 'icons'))


class MainIcon(MenuIcon):

    def __init__(self, tray, win_config, mediaicon_config, host_manager):
        self.__mediaicon_config = mediaicon_config
        MenuIcon.__init__(self, tray)
        win_config.connect(
            "all-workspaces-changed", lambda config: self.update_tooltip()
        )
        mediaicon_config.connect(
            "hide-unmounted-changed", lambda config: self.update_tooltip()
        )
        self.__host_manager = host_manager

    def click(self, time):
        self.__mediaicon_config.hide_unmounted = (
            not self.__mediaicon_config.hide_unmounted 
        )

    def mouse_wheel_up(self, time):
        self.tray.win_config.all_workspaces = True

    def mouse_wheel_down(self, time):
        self.tray.win_config.all_workspaces = False

    def get_icon_names(self):
        return ['computer']

    #def get_custom_menu_items(self):
    #    menu_item = gtk.ImageMenuItem(gtk.STOCK_ADD)
    #    menu_item.set_label(_("Add Host"))
    #    menu_item.connect("activate", self.__add_host)
    #    return [menu_item]

    def __add_host(self, menu_item):
        dialog = HostEditor(self.__host_manager)
        dialog.show()

    def make_tooltip(self):
        if self.tray.win_config.all_workspaces:
            s = _("Scroll down to only show windows of this workspace.")
        else:
            s = _("Scroll up to show windows of all workspaces.")
        if self.__mediaicon_config.hide_unmounted:
            s += '\n' + _("Click to show unmounted volumes.")
        else:
            s += '\n' + _("Click to hide unmounted volumes.")
        return s
