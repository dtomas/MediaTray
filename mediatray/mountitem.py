import os

from gi.repository import Gio, Gtk, GObject, Gdk, GdkPixbuf

import rox
from rox import filer, processes
from rox.options import Option, OptionGroup

from traylib import TARGET_URI_LIST
from traylib.winitem import AWindowsItem
from traylib.icons import FileIcon


icons_dir = os.path.join(rox.app_dir, 'icons')

emblem_rox_mounted = GdkPixbuf.Pixbuf.new_from_file(
    os.path.join(icons_dir, 'rox-mounted.png')
)
emblem_rox_mount = GdkPixbuf.Pixbuf.new_from_file(
    os.path.join(icons_dir, 'rox-mount.png')
)


filer_options = OptionGroup("ROX-Filer", "Options", "rox.sourceforge.net")
o_terminal = Option("menu_xterm", "xterm", filer_options)


class MountItem(AWindowsItem):

    def __init__(self, win_config, screen, volume_monitor):
        AWindowsItem.__init__(self, win_config, screen)

        mount = self.get_mount()
        self.__is_mounted = mount is not None

        volume_monitor.connect("mount-added", self.__mount_added)

        self.__unmounted_handler = mount.connect(
            "unmounted", self.__unmounted
        ) if mount is not None else None

    # Methods from Item:

    def get_drag_source_targets(self):
        return (
            AWindowsItem.get_drag_source_targets(self) +
            [Gtk.TargetEntry.new("text/uri-list", 0, TARGET_URI_LIST)]
        )

    def drag_data_get(self, context, data, info, time):
        """Called when the icon is dragged somewhere."""
        AWindowsItem.drag_data_get(self, context, data, info, time)
        if info == TARGET_URI_LIST:
            if not self.is_mounted:
                return
            data.set_uris(['file://' + self.get_path()])

    def get_icons(self):
        """
        Get the path to the icon.

        This may be a .DirIcon, an icon defined in Windows' autorun.inf or
        an icon from the current icon theme.
        """
        path = self.get_individual_icon_path()
        if path is None:
            return []
        return [FileIcon(path)]

    def get_menu_right(self):
        """
        Create the right-click menu.

        This will contain items to mount/unmount/eject the volume as well as
        submenus for every open window. If there is only one open window,
        the window-related items will be appended to the main menu.
        """
        menu = AWindowsItem.get_menu_right(self)
        if not menu:
            menu = Gtk.Menu()
        else:
            menu.prepend(Gtk.SeparatorMenuItem())
            menu.prepend(Gtk.SeparatorMenuItem())

        if self.is_mounted:
            unmount_item = Gtk.MenuItem.new_with_label(self.unmount_label)
            unmount_item.connect("activate", lambda item: self.unmount())
            menu.prepend(unmount_item)
        else:
            mount_item = Gtk.MenuItem.new_with_label(self.mount_label)
            mount_item.connect("activate", lambda item: self.mount())
            menu.prepend(mount_item)

        menu.prepend(Gtk.SeparatorMenuItem())

        open_in_terminal_item = Gtk.MenuItem.new_with_label(_("Open in terminal"))
        open_in_terminal_item.connect(
            "activate", lambda item: self.open_in_terminal()
        )
        menu.prepend(open_in_terminal_item)

        open_item = Gtk.MenuItem.new_with_label(_("Open"))
        open_item.connect("activate", lambda item: self.open())
        menu.prepend(open_item)
        return menu

    def click(self, time=0):
        """
        When a C{MediaIcon} is clicked, the volume is opened, or - if there
        are open windows - the menu of open windows is shown or - if there is
        only one window - the window is activated.
        """
        if AWindowsItem.click(self, time):
            return True
        self.open()
        return True

    def get_base_name(self):
        """Return the name of the volume."""
        raise NotImplementedError

    def get_emblem(self):
        """Return an emblem indicating whether the volume is mounted or not."""
        return emblem_rox_mounted if self.is_mounted else emblem_rox_mount

    def is_drop_target(self):
        """
        Files can always be dropped on a C{MountItem}, so this returns C{True}.
        """
        return True

    def uris_dropped(self, uri_list, action):
        """
        Called when URIs are dropped on the volume item.

        If the volume is mounted, the files are copied (or moved) to the
        volume. If not, it is mounted and the files will be copied as soon as
        it's mounted.  (see property_changed())"""
        if action == Gdk.DragAction.COPY:
            self.copy(uri_list)
        elif action == Gdk.DragAction.MOVE:
            self.copy(uri_list, True)

    def spring_open(self, time=0):
        """
        When dragging an item over the menu for a while, the volume is opened
        or - if there is only one window - this window is activated, or - if
        there are multiple windows - the windows are cycled through.
        """
        if AWindowsItem.spring_open(self, time):
            return True
        self.open()
        return False

    # Actions

    def _mount(self, on_mount=None):
        raise NotImplementedError

    def _unmount(self, on_unmount=None):
        mount = self.get_mount()

        def unmounted(mount, result):
            if not mount.unmount_with_operation_finish(result):
                return
            if on_unmount:
                on_unmount()
        mount.unmount_with_operation(Gio.MountUnmountFlags.NONE, None, None, unmounted)

    def mount(self, on_mount=None):
        """
        Mount the volume.

        @param on_mount: function which gets called with the volume's
            C{Gio.Mount} object when the volume has been mounted.
        """
        if self.is_mounted:
            # Already mounted.
            return
        self._mount(on_mount=on_mount)

    def unmount(self, on_unmount=None):
        """Unmount the volume."""
        if not self.is_mounted:
            # Already unmounted.
            return

        if self.window_items:
            windows = {item.window for item in self.window_items}
            closed_windows = set()

            def window_closed(screen, window):
                closed_windows.add(window)
                if closed_windows.intersection(windows) == windows:
                    self.screen.disconnect(window_closed_handler)
                    self._unmount(on_unmount=on_unmount)

            window_closed_handler = self.screen.connect(
                "window-closed", window_closed
            )
            for item in self.window_items:
                item.window.close(0)
        else:
            self._unmount(on_unmount=on_unmount)

    def open(self):
        """Open the volume's mount point in ROX-Filer."""

        def open():
            filer.open_dir(self.get_path())

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
            os.chdir(self.get_path())
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
                To={'File': self.get_path()}
            )

        if not self.is_mounted:
            self._mount(on_mount=copy)
        else:
            copy()

    # Methods to be implemented by subclasses:

    def get_mount(self):
        raise NotImplementedError

    def get_mounted_message(self):
        return None

    def get_unmounted_message(self):
        return None

    def get_added_message(self):
        return None

    def get_removed_message(self):
        return None

    def get_removed_detail(self):
        return None

    # Signal handlers

    def __mount_added(self, volume_manager, mount):
        mountpoint = mount.get_root()
        icon_mount = self.get_mount()
        if icon_mount is None:
            return
        if icon_mount.get_root() != mountpoint:
            return
        self.__is_mounted = True
        self.changed("icon", "emblem")
        self.__unmounted_handler = mount.connect(
            "unmounted", self.__unmounted
        )
        self.emit("mounted")

    def __unmounted(self, mount):
        self.__is_mounted = False
        self.changed("emblem")
        for item in self.window_items:
            item.window.close(0)
        if self.__unmounted_handler is not None:
            mount.disconnect(self.__unmounted_handler)
            self.__unmounted_handler = None
        self.emit("unmounted")

    # Icon handling

    def get_individual_icon_path(self):
        """Get the path of the .DirIcon."""
        path = self.get_path()
        if path is None:
            return None

        # Try to read diricon.
        icon_path = os.path.join(path, '.DirIcon')
        if os.access(icon_path, os.R_OK):
            return icon_path

        return None

    @property
    def is_mounted(self):
        return self.__is_mounted

    mountitem_config = property(lambda self: self.__mountitem_config)
    """C{MountItem}-related configuration."""


GObject.type_register(MountItem)
GObject.signal_new(
    "mounted", MountItem, GObject.SignalFlags.RUN_FIRST, None, ()
)
GObject.signal_new(
    "unmounted", MountItem, GObject.SignalFlags.RUN_FIRST, None, ()
)
