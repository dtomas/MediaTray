import os

import gio
import gtk

import rox

from mediatray.mounticon import MountIcon
from mediatray.host_editor import HostEditor


class HostIcon(MountIcon):

    def __init__(self, icon_config, win_config, screen, host_manager, host,
                 volume_monitor):
        self.__host_manager = host_manager
        self.__host = host
        self.__file = gio.File(host.uri)
        MountIcon.__init__(self, icon_config, win_config, screen,
                           volume_monitor)

        self.mount_label = _("Connect")
        self.unmount_label = _("Disconnect")
        self.__host.connect("changed", self.__host_changed)

    def __host_changed(self, host):
        def update_file():
            self.__file = gio.File(host.uri)
            self.update_name()
            self.update_tooltip()
            self.update_emblem()
        if self.is_mounted:
            self.unmount(on_unmount=update_file)
        else:
            update_file()

    def get_mount(self):
        try:
            return self.__file.find_enclosing_mount(None)
        except gio.Error:
            return None

    def get_mounted_message(self):
        return _("Connected to host \"%s\".") % self.name

    def get_unmounted_message(self):
        return _("Disconnected from host \"%s\".") % self.name

    def make_path(self):
        return self.__file.get_path()

    def _mount(self, on_mount=None):
        def mounted(data, result):
            if self.__file.mount_enclosing_volume_finish(result) and on_mount:
                on_mount()
        self.__file.mount_enclosing_volume(gtk.MountOperation(), mounted)

    def get_fallback_icon_path(self):
        return os.path.join(rox.app_dir, 'icons', 'drive-harddisk.png')

    def get_icon_names(self):
        return ['network-server']

    def make_name(self):
        return self.__host.name

    def get_menu_right(self):
        menu = MountIcon.get_menu_right(self)

        menu.append(gtk.SeparatorMenuItem())

        def edit(menu_item):
            HostEditor(self.__host_manager, self.__host).show()

        menu_item = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        menu_item.connect("activate", edit)
        menu.append(menu_item)

        menu.append(gtk.SeparatorMenuItem())

        def remove(menu_item):
            if rox.confirm(
                    _("Really remove host %s?") % self.__host.name,
                    gtk.STOCK_REMOVE):
                self.__host.remove()

        menu_item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        menu_item.connect("activate", remove)
        menu.append(menu_item)

        return menu
