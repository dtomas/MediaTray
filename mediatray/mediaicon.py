import os, gtk, struct, gio
from rox import filer

from traylib import *
from traylib.winicon import WinIcon
from traylib.winmenu import get_filer_window_path


class MediaIcon(WinIcon):

    def __init__(self, icon_config, win_config, volume):
        WinIcon.__init__(self, icon_config, win_config)

        self.__volume = volume

        self.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                            [("application/x-wnck-window-id", 
                                0,
                                TARGET_WNCK_WINDOW_ID)], 
                            gtk.gdk.ACTION_MOVE)
        self.connect("drag-data-get", self.__drag_data_get)
        self.__volume.connect("removed", self.__removed)

        if self.__volume.get_mount() is not None:
            self.__unmount_handler = self.__volume.get_mount().connect(
                "unmounted", self.__unmounted
            )

        self.update_visibility()
        self.update_icon()
        self.update_name()
        self.update_tooltip()

    def __removed(self, volume):
        for window in self.windows:
            window.close(0)

    def __drag_data_get(self, widget, context, data, info, time):
        if not self.visible_windows:
            return
        xid = self.visible_windows[0].get_xid()
        data.set(data.target, 8, apply(struct.pack, ['1i', xid]))

    def get_menu_right(self):
        menu = WinIcon.get_menu_right(self)
        if not menu:
            menu = gtk.Menu()
        else:
            menu.prepend(gtk.SeparatorMenuItem())
            menu.prepend(gtk.SeparatorMenuItem())

        if self.__volume.can_eject():
            eject_item = gtk.ImageMenuItem()
            eject_item.set_label(_("Eject"))
            eject_image = gtk.image_new_from_pixbuf(
                ICON_THEME.load_icon("media-eject", gtk.ICON_SIZE_MENU, 0)
            )
            eject_item.set_image(eject_image)
            eject_item.connect("activate", self.__eject) 
            menu.prepend(eject_item)

        if self.__volume.can_mount():
            if self.__volume.get_mount():
                unmount_item = gtk.ImageMenuItem()
                unmount_item.set_label(_("Unmount"))
                unmount_image = gtk.image_new_from_pixbuf(
                    ICON_THEME.load_icon("rox-mount", gtk.ICON_SIZE_MENU, 0)
                )
                unmount_item.set_image(unmount_image)
                unmount_item.connect("activate", self.__unmount) 
                menu.prepend(unmount_item)
            else:
                mount_item = gtk.ImageMenuItem()
                mount_item.set_label(_("Mount"))
                mount_image = gtk.image_new_from_pixbuf(
                    ICON_THEME.load_icon("rox-mounted", gtk.ICON_SIZE_MENU, 0)
                )
                mount_item.connect("activate", self.__mount)
                mount_item.set_image(mount_image)
                menu.prepend(mount_item)

            menu.prepend(gtk.SeparatorMenuItem())
            open_item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
            open_item.connect("activate", self.__open)
            menu.prepend(open_item)
        return menu

    def __unmounted(self, mount):
        mount.disconnect(self.__unmount_handler)
        self.__removed(self.__volume)

    def __mount(self, menu_item=None, on_mount=None):
        def mounted(volume, result):
            if self.__volume.mount_finish(result):
                if on_mount is not None:
                    on_mount(self.__volume.get_mount())
                self.__unmount_handler = volume.get_mount().connect(
                    "unmounted", self.__unmounted
                )
        self.__volume.mount(None, mounted)

    def __unmount(self, menu_item=None):
        mount = self.__volume.get_mount()

        def unmounted(mount, result):
            mount.unmount_finish(result)
        mount.unmount(unmounted)

    def __open(self, menu_item=None):
        mount = self.__volume.get_mount()

        def open(mount):
            filer.open_dir(mount.get_root().get_path())

        if not mount:
            self.__mount(on_mount=open)
        else:
            open(mount)

    def __eject(self, menu_item):
        def ejected(volume, result):
            self.__volume.eject_finish(result)
        self.__volume.eject(ejected)

    def click(self, time=0L):
        if WinIcon.click(self):
            return True
        self.__open()
        return True

    def get_icon_names(self):
        return self.__volume.get_icon().get_names()

    def make_name(self):
        return self.__volume.get_name()

    def should_hide_if_no_visible_windows(self):
        return False

    def should_have_window(self, window):
        mount = self.__volume.get_mount()
        if mount is None:
            return False
        root = mount.get_root()
        path = os.path.expanduser(get_filer_window_path(window))
        return path.startswith(root.get_path())
