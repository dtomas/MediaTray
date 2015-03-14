import os, gtk, struct, gio
from xml.sax.saxutils import escape

from rox import filer

from traylib import *
from traylib.winicon import WinIcon
from traylib.winmenu import get_filer_window_path


icons_dir = os.path.join(rox.app_dir, 'icons')

emblem_rox_mounted = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mounted.png')
)
emblem_rox_mount = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mount.png')
)


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

        self.__unmount_handler = self.__volume.get_mount().connect(
            "unmounted", self.__unmounted
        ) if self.__volume.get_mount() is not None else None

        self.update_visibility()
        self.update_icon()
        self.update_name()
        self.update_emblem()
        self.update_tooltip()
        self.update_is_drop_target()

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
                unmount_item = gtk.ImageMenuItem(gtk.STOCK_CANCEL)
                unmount_item.set_label(_("Unmount"))
                unmount_item.connect("activate", self.__unmount) 
                menu.prepend(unmount_item)
            else:
                mount_item = gtk.ImageMenuItem(gtk.STOCK_YES)
                mount_item.set_label(_("Mount"))
                mount_item.connect("activate", self.__mount)
                menu.prepend(mount_item)

            menu.prepend(gtk.SeparatorMenuItem())
            open_item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
            open_item.connect("activate", self.__open)
            menu.prepend(open_item)
        return menu

    def __unmounted(self, mount):
        self.update_emblem()
        mount.disconnect(self.__unmount_handler)
        self.__unmount_handler = None
        self.__removed(self.__volume)

    def __mount(self, menu_item=None, on_mount=None):
        def mounted(volume, result):
            if self.__volume.mount_finish(result):
                if on_mount is not None:
                    on_mount(self.__volume.get_mount())
                if self.__unmount_handler is not None:
                    volume.get_mount().disconnect(self.__unmount_handler)
                self.__unmount_handler = volume.get_mount().connect(
                    "unmounted", self.__unmounted
                )
                self.update_emblem()
        self.__volume.mount(gtk.MountOperation(), mounted)

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
        # Fallback icon, shipped with MediaTray.
        icons = ["drive-harddisk"]
        icon = self.__volume.get_icon()
        if icon is not None and hasattr(icon, 'get_names'):
            icons = icon.get_names() + icons
        return icons

    def make_name(self):
        return self.__volume.get_name()

    def make_emblem(self):
        if not self.__volume.can_mount():
            return None
        return (
            emblem_rox_mount if self.__volume.get_mount() is None
            else emblem_rox_mounted
        )

    def should_hide_if_no_visible_windows(self):
        return False

    def should_have_window(self, window):
        mount = self.__volume.get_mount()
        if mount is None:
            return False
        root = mount.get_root()
        if root is None:
            return False
        root_path = root.get_path()
        path = os.path.expanduser(get_filer_window_path(window))
        return (
            path == root.get_path() or
                os.path.isdir(path) and
                os.stat(root_path).st_dev == os.stat(path).st_dev
        )

    def menu_has_kill(self):
        return False

    def make_is_drop_target(self):
        return True

    def uris_dropped(self, uri_list, action):
        """
        Called when URIs are dropped on the volume item.

        If the volume is mounted, the files are copied (or moved) to the
        volume. If not, it is mounted and the files will be copied as soon as
        it's mounted.  (see property_changed())"""
        if self.__volume.get_mount() is not None:
            if action == gtk.gdk.ACTION_COPY:
                self.__copy(uri_list)
            elif action == gtk.gdk.ACTION_MOVE:
                self.__copy(uri_list, True)
        else:
            if action == gtk.gdk.ACTION_COPY:
                self.mount(on_mount=partial(
                    self.__copy, uri_list=uri_list, move=False
                ))
            elif action == gtk.gdk.ACTION_MOVE:
                self.mount(on_mount=partial(
                    self.__copy, uri_list=uri_list, move=True
                ))

    def __copy(self, uri_list, move=False):
        """Copy or move uris to the volume (via ROX-Filer).""" 
        assert self.__volume.get_mount() is not None
        assert self.__volume.get_mount().get_root() is not None
        if move:
            action = 'Move'
        else:
            action = 'Copy'
        f = os.popen('rox --RPC', 'w')
        xml = (
            '<?xml version="1.0"?>'
            '<env:Envelope xmlns:env="http://www.w3.org/2001/12/soap-envelope">'
            '<env:Body xmlns="http://rox.sourceforge.net/SOAP/ROX-Filer">'
            '<%s><From>' % action
        )
        for uri in uri_list:
            if not uri.startswith('file'):
                    continue
            path = rox.get_local_path(uri)
            xml += '<File>%s</File>' % escape(path)
        xml += (
            '</From><To>%s</To></%s></env:Body></env:Envelope>' % (
                escape(self.__volume.get_mount().get_root().get_path()), action
            )
        )
        f.write(xml)
        f.close()

    def spring_open(self, time = 0L):
        if WinIcon.spring_open(self, time):
            return True
        self.__open()
        return False
