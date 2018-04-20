from gi.repository import Gio
from gi.repository import Gtk

import rox

from traylib.icons import ThemedIcon

from mediatray.mountitem import MountItem
from mediatray.host_editor import HostEditor


class HostItem(MountItem):

    def __init__(self, win_config, screen, host_manager, host, volume_monitor):
        self.__host_manager = host_manager
        self.__host = host
        self.__file = Gio.File(host.uri)
        MountItem.__init__(self, win_config, screen, volume_monitor)

        self.mount_label = _("Connect")
        self.unmount_label = _("Disconnect")
        self.__host.connect("changed", self.__host_changed)

    def __host_changed(self, host):
        def update_file():
            self.__file = Gio.File(host.uri)
            self.changed("name", "emblem")
        if self.is_mounted:
            self.unmount(on_unmount=update_file)
        else:
            update_file()

    def get_mount(self):
        try:
            return self.__file.find_enclosing_mount(None)
        except Gio.Error:
            return None

    def get_mounted_message(self):
        return _("Connected to host \"%s\".") % self.get_base_name()

    def get_unmounted_message(self):
        return _("Disconnected from host \"%s\".") % self.get_base_name()

    def get_path(self):
        return self.__file.get_path()

    def _mount(self, on_mount=None):
        def mounted(data, result):
            if self.__file.mount_enclosing_volume_finish(result) and on_mount:
                on_mount()
        self.__file.mount_enclosing_volume(Gtk.MountOperation(), mounted)

    def get_icons(self):
        return [ThemedIcon('network-server')]

    def get_base_name(self):
        return self.__host.name

    def get_menu_right(self):
        menu = MountItem.get_menu_right(self)

        menu.append(Gtk.SeparatorMenuItem())

        def edit(menu_item):
            HostEditor(self.__host_manager, self.__host).show()

        menu_item = Gtk.MenuItem.new_with_label(_("Edit"))
        menu_item.connect("activate", edit)
        menu.append(menu_item)

        menu.append(Gtk.SeparatorMenuItem())

        def remove(menu_item):
            if rox.confirm(
                    _("Really remove host %s?") % self.__host.name,
                    Gtk.STOCK_REMOVE):
                self.__host.remove()

        menu_item = Gtk.MenuItem.new_with_label(_("Remove"))
        menu_item.connect("activate", remove)
        menu.append(menu_item)

        return menu

    def is_visible(self):
        return True

    host = property(lambda self: self.__host)
