import os

import rox

import gtk

from traylib import ICON_THEME
from traylib.main_item import MainItem
from traylib.icons import ThemedIcon

from mediatray.host_editor import HostEditor


ICON_THEME.append_search_path(os.path.join(rox.app_dir, 'icons'))


class MediaTrayMainItem(MainItem):

    def __init__(self, tray, tray_config, icon_config, win_config,
                 mediaitem_config, host_manager):
        self.__mediaitem_config = mediaitem_config
        self.__win_config = win_config
        MainItem.__init__(self, tray, tray_config, icon_config)
        self.__win_config_signal_handlers = [
            win_config.connect(
                "all-workspaces-changed", lambda config: self.changed("name")
            )
        ]
        self.__mediaitem_config_signal_handlers = [
            mediaitem_config.connect(
                "hide-unmounted-changed", lambda config: self.changed("name")
            )
        ]
        self.__host_manager = host_manager
        self.connect("destroyed", self.__destroyed)

    def __destroyed(self, item):
        for handler in self.__win_config_signal_handlers:
            self.__win_config.disconnect(handler)
        for handler in self.__mediaitem_config_signal_handlers:
            self.__mediaitem_config.disconnect(handler)

    def click(self, time):
        self.__mediaitem_config.hide_unmounted = (
            not self.__mediaitem_config.hide_unmounted 
        )

    def mouse_wheel_up(self, time):
        self.__win_config.all_workspaces = True

    def mouse_wheel_down(self, time):
        self.__win_config.all_workspaces = False

    def get_icons(self):
        return [ThemedIcon('computer')]

    #def get_custom_menu_items(self):
    #    menu_item = gtk.ImageMenuItem(gtk.STOCK_ADD)
    #    menu_item.set_label(_("Add Host"))
    #    menu_item.connect("activate", self.__add_host)
    #    return [menu_item]

    def __add_host(self, menu_item):
        dialog = HostEditor(self.__host_manager)
        dialog.show()

    def get_name(self):
        if self.__win_config.all_workspaces:
            s = _("Scroll down to only show windows of this workspace.")
        else:
            s = _("Scroll up to show windows of all workspaces.")
        if self.__mediaitem_config.hide_unmounted:
            s += '\n' + _("Click to show unmounted volumes.")
        else:
            s += '\n' + _("Click to hide unmounted volumes.")
        return s
