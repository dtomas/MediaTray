import os

import gio
import gtk

import rox

from mediatray.mounticon import MountIcon


class HostIcon(MountIcon):

    def __init__(self, icon_config, win_config, mounticon_config, screen,
                 host):
        self.__host = host
        self.__file = gio.File(host.uri)
        try:
            mount = self.__file.find_enclosing_mount(None)
        except gio.Error:
            self.__is_mounted = False
        else:
            self.__is_mounted = True
            self.__unmounted_handler = mount.connect(
                "unmounted", self.__unmounted
            )
        MountIcon.__init__(self, icon_config, win_config, mounticon_config,
                           screen)

        self.mount_label = _("Connect")
        self.unmount_label = _("Disconnect")

    def get_mount(self):
        try:
            return self.__file.find_enclosing_mount(None)
        except gio.Error:
            return None

    @property
    def mountpoint(self):
        return self.__file.get_path()

    @property
    def is_mounted(self):
        return self.__is_mounted

    def _mount(self, on_mount=None):
        def mounted(data, result):
            if self.__file.mount_enclosing_volume_finish(result) and on_mount:
                on_mount()
        self.__file.mount_enclosing_volume(gtk.MountOperation(), mounted)

    def _unmount(self):
        mount = self.get_mount()

        def unmounted(mount, result):
            mount.unmount_finish(result)
        mount.unmount(unmounted)

    def mounted(self):
        """Called when the volume has been mounted."""
        self.__is_mounted = True
        MountIcon.mounted(self)
        self.__unmounted_handler = self.get_mount().connect(
            "unmounted", self.__unmounted
        )

    def __unmounted(self, mount):
        self.__is_mounted = False
        self.unmounted(mount.get_root().get_path())
        mount.disconnect(self.__unmounted_handler)
        self.__unmounted_handler = None

    def get_fallback_icon_path(self):
        return os.path.join(rox.app_dir, 'icons', 'drive-harddisk.png')

    def get_icon_names(self):
        return ['network-server']

    def make_name(self):
        return self.__host.name

    def get_menu_right(self):
        menu = MountIcon.get_menu_right(self)

        menu.append(gtk.SeparatorMenuItem())

        menu_item = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        menu_item.connect("activate", lambda menu_item: self.__host.remove())
        menu.append(menu_item)

        return menu
