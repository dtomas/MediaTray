import os
import re
import struct
import json

import gtk

import gio

import rox
from rox import filer, processes
from rox.options import Option, OptionGroup

from traylib import TARGET_WNCK_WINDOW_ID, TARGET_URI_LIST, ICON_THEME
from traylib.winicon import WinIcon
from traylib.winmenu import get_filer_window_path

from mediatray.config import config_dir
from mediatray.mounticon_config import AUTOMOUNT, AUTOOPEN


icons_dir = os.path.join(rox.app_dir, 'icons')

emblem_rox_mounted = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mounted.png')
)
emblem_rox_mount = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mount.png')
)


_volumes_on_pinboard_path = os.path.join(config_dir, 'volumes_on_pinboard')

volumes_on_pinboard = []


# remove non-existent volumes from pinboard
try:
    f = open(_volumes_on_pinboard_path, 'r')
    try:
        volumes_on_pinboard = json.load(f)
    except ValueError:
        # Unreadable file, remove it.
        os.unlink(_volumes_on_pinboard_path)
    finally:
        f.close()
except IOError:
    pass


for path in volumes_on_pinboard:
    if not os.path.isdir(path):
        filer.rpc.PinboardRemove(Path=path)
        filer.rpc.UnsetIcon(Path=path)

if volumes_on_pinboard:
    volumes_on_pinboard = []
    f = open(_volumes_on_pinboard_path, 'w')
    try:
        json.dump(volumes_on_pinboard, f)
    finally:
        f.close()


filer_options = OptionGroup("ROX-Filer", "Options", "rox.sourceforge.net")
o_terminal = Option("menu_xterm", "xterm", filer_options)


_terminal_title_re = re.compile(r'^.+\@.+\: (?P<path>.+)$')


class MountIcon(WinIcon):

    def __init__(self, icon_config, win_config, mounticon_config, screen):
        WinIcon.__init__(self, icon_config, win_config, screen)

        self.__mounticon_config = mounticon_config
        mounticon_config.add_configurable(self)

        self.__is_on_pinboard = False

        self.drag_source_set(
            gtk.gdk.BUTTON1_MASK, [
                ("application/x-wnck-window-id", 0, TARGET_WNCK_WINDOW_ID),
                ("text/uri-list", 0, TARGET_URI_LIST)
            ], gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK
        )
        self.connect("drag-data-get", self.__drag_data_get)

        self.__set_icon(self.get_icon_path())

        mount = self.get_mount()
        self.__is_mounted = mount is not None

        self.__unmounted_handler = mount.connect(
            "unmounted", self.__unmounted
        ) if mount is not None else None

        self.update_visibility()
        self.update_icon()
        self.update_name()
        self.update_emblem()
        self.update_tooltip()
        self.update_is_drop_target()

        self.add_to_pinboard()

    def get_mount(self):
        raise NotImplementedError

    @property
    def mountpoint(self):
        """The volume's mount point or C{None} if the volume is not mounted."""
        raise NotImplementedError

    @property
    def is_mounted(self):
        return self.__is_mounted


    # Actions

    def _mount(self, on_mount=None):
        raise NotImplementedError

    def _unmount(self):
        mount = self.get_mount()

        def unmounted(mount, result):
            mount.unmount_finish(result)
        mount.unmount(unmounted)

    def mount(self, on_mount=None):
        """
        Mount the volume.

        @param on_mount: function which gets called with the volume's
            C{gio.Mount} object when the volume has been mounted.
        """
        if self.is_mounted:
            # Already mounted.
            return
        self._mount(on_mount=on_mount)

    def unmount(self):
        """Unmount the volume."""
        if not self.is_mounted:
            # Already unmounted.
            return

        windows = set(self.windows)
        if windows:
            closed_windows = set()

            def window_closed(screen, window):
                closed_windows.add(window)
                if closed_windows.intersection(windows) == windows:
                    self.screen.disconnect(window_closed_handler)
                    self._unmount()

            window_closed_handler = self.screen.connect(
                "window-closed", window_closed
            )
            for window in self.windows:
                window.close(0)
        else:
            self._unmount()

    def open(self):
        """Open the volume's mount point in ROX-Filer."""

        def open():
            filer.open_dir(self.mountpoint)

        if not self.is_mounted:
            self.mount(on_mount=open)
        else:
            open()

    def open_in_terminal(self):
        """
        Open the volume's mount point in a terminal.
        
        The terminal command is read from ROX-Filer's menu_xterm option.
        """
        def open():
            terminal_cmd = o_terminal.value.split()
            cwd = os.getcwd()
            os.chdir(self.mountpoint)
            processes.PipeThroughCommand(terminal_cmd, None, None).start()
            os.chdir(cwd)

        if not self.is_mounted:
            self._mount(on_mount=open)
        else:
            open()

    def copy(self, uri_list, move=False):
        """Copy or move uris to the volume (via ROX-Filer).""" 

        def copy():
            if move:
                action = filer.rpc.Move
            else:
                action = filer.rpc.Copy
            action(
                From={'File': [rox.get_local_path(uri) for uri in uri_list]},
                To={'File': self.mountpoint}
            )

        if not self.is_mounted:
            self._mount(on_mount=copy)
        else:
            copy(mount)


    # Methods called when MediaIconConfig has changed.

    def update_option_pin(self):
        """Called when the pin option has changed."""
        if self.__mediaicon_config.pin:
            self.add_to_pinboard()
        else:
            self.remove_from_pinboard(self.mountpoint)

    def update_option_pin_x(self):
        """Called when the pin_x option has changed."""
        self.remove_from_pinboard(self.mountpoint)
        self.add_to_pinboard()

    def update_option_pin_y(self):
        """Called when the pin_y option has changed."""
        self.remove_from_pinboard(self.mountpoint)
        self.add_to_pinboard()


    # Signal handlers

    def __drag_data_get(self, widget, context, data, info, time):
        """Called when the icon is dragged somewhere."""
        if info == TARGET_WNCK_WINDOW_ID:
            if not self.visible_windows:
                return
            xid = self.visible_windows[0].get_xid()
            data.set(data.target, 8, apply(struct.pack, ['1i', xid]))
        else:
            if not self.is_mounted:
                return
            data.set_uris(['file://' + self.mountpoint])

    def removed(self, mountpoint):
        """Called when the mountable has been removed."""
        for window in self.windows:
            window.close(0)
        self.remove_from_pinboard(mountpoint)

    def mounted(self):
        """Called when the volume has been mounted."""
        self.__is_mounted = True
        self.update_icon()
        self.update_emblem()
        self.__set_icon(self.get_icon_path())
        self.add_to_pinboard()
        self.__unmounted_handler = self.get_mount().connect(
            "unmounted", self.__unmounted
        )

    def __unmounted(self, mount):
        self.__is_mounted = False
        self.unmounted(mount.get_root().get_path())
        mount.disconnect(self.__unmounted_handler)
        self.__unmounted_handler = None

    def unmounted(self, mountpoint):
        """Called when the volume has been unmounted."""
        self.update_emblem()
        self.removed(mountpoint)


    # Pinboard

    def add_to_pinboard(self):
        """
        Add the volume to the pinboard.

        Only works if the volume is mounted and the pin option is set.
        """
        if self.__is_on_pinboard:
            return
        if not self.mounticon_config.pin:
            return
        root_path = self.mountpoint
        if root_path is None:
            return
        filer.rpc.PinboardAdd(
            Path=root_path,
            Label=self.name,
            X=self.mounticon_config.pin_x,
            Y=self.mounticon_config.pin_y,
            Update=1,
        )
        if root_path not in volumes_on_pinboard:
            volumes_on_pinboard.append(root_path)
            f = open(_volumes_on_pinboard_path, 'w')
            try:
                json.dump(volumes_on_pinboard, f)
            finally:
                f.close()
        self.__is_on_pinboard = True

    def remove_from_pinboard(self, mountpoint, unset_icon=False):
        """Remove the volume from the pinboard."""
        filer.rpc.PinboardRemove(Path=mountpoint)
        filer.rpc.UnsetIcon(Path=mountpoint)
        if mountpoint in volumes_on_pinboard:
            volumes_on_pinboard.remove(mountpoint)
            f = open(_volumes_on_pinboard_path, 'w')
            try:
                json.dump(volumes_on_pinboard, f)
            finally:
                f.close()
        self.__is_on_pinboard = False


    # Icon handling

    def __set_icon(self, icon_path):
        """Set the icon to use for the mount point in ROX-Filer."""
        if icon_path is None:
            return
        root_path = self.mountpoint
        if root_path is None:
            return
        filer.rpc.SetIcon(Path=root_path, Icon=icon_path)

    def get_individual_icon_path(self):
        """Get the path of the .DirIcon."""
        root_path = self.mountpoint
        if root_path is None:
            return None

        # Try to read diricon.
        icon_path = os.path.join(root_path, '.DirIcon')
        if os.access(icon_path, os.R_OK):
            return icon_path

        return None

    def get_fallback_icon_path():
        raise NotImplementedError


    # Methods overridden from WinIcon.

    def should_hide_if_no_visible_windows(self):
        """
        A mediaicon should be shown regardless of its visible windows.
        
        So this always returns C{False}.
        """
        return False

    def should_have_window(self, window):
        """
        Determine whether the given window should show up in the menu or not.

        Recognizes ROX-Filer as well as Terminal windows.
        """
        root_path = self.mountpoint
        if root_path is None:
            return False
        class_group = window.get_class_group().get_name()
        path = os.path.expanduser(get_filer_window_path(window))
        if not path:
            match = _terminal_title_re.match(window.get_name())
            if match is None:
                return None
            path = match.groupdict()['path']
        if not path:
            return False
        return (
            path == root_path or
                os.path.isdir(path) and
                os.stat(root_path).st_dev == os.stat(path).st_dev
        )

    def menu_has_kill(self):
        """Hide the 'Force Quit' button in the winmenu."""
        return False


    # Methods overridden from Icon.

    def get_icon_path(self):
        """
        Get the path to the icon.
        
        This may be a .DirIcon, an icon defined in Windows' autorun.inf or
        an icon from the current icon theme.
        """
        icon_path = self.get_individual_icon_path()
        if icon_path is not None:
            return icon_path

        for icon_name in self.icon_names:
            icon_info = ICON_THEME.lookup_icon(icon_name, 48, 0)
            if icon_info is not None:
                icon_path = icon_info.get_filename()
                #icon_info.free()
                break
        else:
            icon_path = self.get_fallback_icon_path()
        return icon_path

    def get_menu_right(self):
        """
        Create the right-click menu.

        This will contain items to mount/unmount/eject the volume as well as
        submenus for every open window. If there is only one open window,
        the window-related items will be appended to the main menu.
        """
        menu = WinIcon.get_menu_right(self)
        if not menu:
            menu = gtk.Menu()
        else:
            menu.prepend(gtk.SeparatorMenuItem())
            menu.prepend(gtk.SeparatorMenuItem())

        if self.is_mounted:
            unmount_item = gtk.ImageMenuItem(gtk.STOCK_CANCEL)
            unmount_item.set_label(self.unmount_label)
            unmount_item.connect("activate", lambda item: self.unmount()) 
            menu.prepend(unmount_item)
        else:
            mount_item = gtk.ImageMenuItem(gtk.STOCK_YES)
            mount_item.set_label(self.mount_label)
            mount_item.connect("activate", lambda item: self.mount())
            menu.prepend(mount_item)

        menu.prepend(gtk.SeparatorMenuItem())

        open_in_terminal_item = gtk.ImageMenuItem(_("Open in terminal"))
        open_in_terminal_image = gtk.image_new_from_pixbuf(
            ICON_THEME.load_icon("utilities-terminal",
                                 gtk.ICON_SIZE_MENU, 0)
        )
        open_in_terminal_item.set_image(open_in_terminal_image)
        open_in_terminal_item.connect(
            "activate", lambda item: self.open_in_terminal()
        )
        menu.prepend(open_in_terminal_item)

        open_item = gtk.ImageMenuItem(gtk.STOCK_OPEN)
        open_item.connect("activate", lambda item: self.open())
        menu.prepend(open_item)
        return menu

    def click(self, time=0L):
        """
        When a C{MediaIcon} is clicked, the volume is opened, or - if there
        are open windows - the menu of open windows is shown or - if there is
        only one window - the window is activated.
        """
        if WinIcon.click(self):
            return True
        self.open()
        return True

    def get_icon_names(self):
        """Get the icon names for the volume."""
        raise NotImplementedError

    def make_name(self):
        """Return the name of the volume."""
        raise NotImplementedError

    def make_emblem(self):
        """Return an emblem indicating whether the volume is mounted or not."""
        return emblem_rox_mounted if self.is_mounted else emblem_rox_mount

    def make_is_drop_target(self):
        """
        Files can always be dropped on a C{MediaIcon}, so this returns C{True}.
        """
        return True

    def uris_dropped(self, uri_list, action):
        """
        Called when URIs are dropped on the volume item.

        If the volume is mounted, the files are copied (or moved) to the
        volume. If not, it is mounted and the files will be copied as soon as
        it's mounted.  (see property_changed())"""
        if action == gtk.gdk.ACTION_COPY:
            self.copy(uri_list)
        elif action == gtk.gdk.ACTION_MOVE:
            self.copy(uri_list, True)

    def spring_open(self, time = 0L):
        """
        When dragging an item over the menu for a while, the volume is opened
        or - if there is only one window - this window is activated, or - if
        there are multiple windows - the windows are cycled through.
        """
        if WinIcon.spring_open(self, time):
            return True
        self.open()
        return False

    mounticon_config = property(lambda self : self.__mounticon_config)
    """C{MediaIcon}-related configuration."""
