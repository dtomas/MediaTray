import os
import re
import struct
import json
from xml.sax.saxutils import escape
from ConfigParser import RawConfigParser, NoOptionError

import gtk

import gio

import rox
from rox import filer, processes
from rox.options import Option, OptionGroup

from traylib import TARGET_WNCK_WINDOW_ID, TARGET_URI_LIST, ICON_THEME
from traylib.winicon import WinIcon
from traylib.winmenu import get_filer_window_path

from mediatray.config import config_dir
from mediatray.mediaicon_config import AUTOMOUNT, AUTOOPEN


icons_dir = os.path.join(rox.app_dir, 'icons')

emblem_rox_mounted = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mounted.png')
)
emblem_rox_mount = gtk.gdk.pixbuf_new_from_file(
    os.path.join(icons_dir, 'rox-mount.png')
)


SECTION_WINDOWS_AUTORUN = 'autorun'


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
        f = os.popen('rox --RPC', 'w')
        f.write(
            '<?xml version="1.0"?>'
            '<env:Envelope xmlns:env="http://www.w3.org/2001/12/soap-envelope">'
                '<env:Body xmlns="http://rox.sourceforge.net/SOAP/ROX-Filer">'
                    '<PinboardRemove>'
                        '<Path>' + escape(path) + '</Path>'
                    '</PinboardRemove>'
                    '<UnsetIcon>'
                        '<Path>' + escape(path) + '</Path>'
                        '</UnsetIcon>'
                '</env:Body>'
                '</env:Envelope>'
        )
        f.close()
		
if volumes_on_pinboard:
    volumes_on_pinboard = []
    f = open(_volumes_on_pinboard_path, 'w')
    try:
        json.dump(volumes_on_pinboard, f)
    finally:
        f.close()


filer_options = OptionGroup("ROX-Filer", "Options", "rox.sourceforge.net")
o_terminal = Option("menu_xterm", "xterm", filer_options)


class WindowsAutoRun(object):
    
    def __init__(self):
        self.__exe = ''
        self.__icon = ''

    @property
    def icon(self):
        return self.__icon

    @property
    def exe(self):
        return self.__exe

    @exe.setter
    def exe(self, exe):
        self.__exe = (
            None if exe is None
            else exe.strip(' \\').replace('\\', os.path.sep)
        )
            
    @property
    def icon(self):
        return self.__icon

    @icon.setter
    def icon(self, icon):
        self.__icon = (
            None if icon is None
            else icon.strip(' \\').replace('\\', os.path.sep)
        )


def get_case_sensitive_path(path, root = '/'):
    """Search for a case sensitive path equivalent to the given path.
    root is the portion of the path that exists."""
    if path == root:
        return root
    dirname, basename = os.path.split(path)
    basename = basename.lower()
    for filename in os.listdir(dirname):
        if filename.lower() == basename:
            return os.path.join(get_case_sensitive_path(dirname), filename)
    return ''


_terminal_title_re = re.compile(r'^.+\@.+\: (?P<path>.+)$')


class MediaIcon(WinIcon):

    def __init__(self, icon_config, win_config, mediaicon_config, volume,
                 screen):
        WinIcon.__init__(self, icon_config, win_config, screen)

        self.__mediaicon_config = mediaicon_config
        mediaicon_config.add_configurable(self)

        self.__volume = volume
        self.__is_on_pinboard = False

        self.drag_source_set(
            gtk.gdk.BUTTON1_MASK, [
                ("application/x-wnck-window-id", 0, TARGET_WNCK_WINDOW_ID),
                ("text/uri-list", 0, TARGET_URI_LIST)
            ], gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK
        )
        self.connect("drag-data-get", self.__drag_data_get)
        self.__volume.connect("removed", self.__removed)

        mount = self.__volume.get_mount()

        self.add_to_pinboard()
        
        self.__set_icon(self.get_icon_path())

        self.update_visibility()
        self.update_icon()
        self.update_name()
        self.update_emblem()
        self.update_tooltip()
        self.update_is_drop_target()

    @property
    def mountpoint(self):
        """The volume's mount point or C{None} if the volume is not mounted."""
        mount = self.__volume.get_mount()
        if mount is None:
            return None
        root = mount.get_root()
        if root is None:
            # Should never happen, but anyway...
            return None
        return root.get_path()


    # Actions

    def mount(self, on_mount=None):
        """
        Mount the volume.

        @param on_mount: function which gets called with the volume's
            C{gio.Mount} object when the volume has been mounted.
        """
        if self.__volume.get_mount() is not None:
            # Already mounted.
            return
        def mounted(volume, result):
            if not volume.mount_finish(result):
                return
            mount = volume.get_mount()
            if on_mount is not None:
                on_mount(mount)
            self.mounted()
        self.__volume.mount(gtk.MountOperation(), mounted)

    def unmount(self):
        """Unmount the volume."""
        mount = self.__volume.get_mount()
        if mount is None:
            # Already unmounted.
            return

        def unmounted(mount, result):
            if not mount.unmount_finish(result):
                return
            self.unmounted(mount)

        windows = set(self.windows)
        if windows:
            closed_windows = set()

            def window_closed(screen, window):
                closed_windows.add(window)
                if closed_windows.intersection(windows) == windows:
                    self.screen.disconnect(window_closed_handler)
                    mount.unmount(unmounted)

            window_closed_handler = self.screen.connect(
                "window-closed", window_closed
            )
            for window in self.windows:
                window.close(0)
        else:
            mount.unmount(unmounted)

    def open(self):
        """Open the volume's mount point in ROX-Filer."""
        mount = self.__volume.get_mount()

        def open(mount):
            filer.open_dir(mount.get_root().get_path())

        if mount is None:
            self.mount(on_mount=open)
        else:
            open(mount)

    def open_in_terminal(self):
        mount = self.__volume.get_mount()

        def open(mount):
            terminal_cmd = o_terminal.value.split()
            cwd = os.getcwd()
            os.chdir(mount.get_root().get_path())
            processes.PipeThroughCommand(terminal_cmd, None, None).start()
            os.chdir(cwd)

        if mount is None:
            self.mount(on_mount=open)
        else:
            open(mount)

    def eject(self):
        """Eject the volume."""
        def ejected(volume, result):
            self.__volume.eject_finish(result)
        self.__volume.eject(ejected)

    def copy(self, uri_list, move=False):
        """Copy or move uris to the volume (via ROX-Filer).""" 
        root_path = self.mountpoint
        if root_path is None:
            return
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


    # Methods called when MediaIconConfig has changed.

    def update_option_pin(self):
        """Called when the pin option has changed."""
        if self.__mediaicon_config.pin:
            self.add_to_pinboard()
        else:
            self.remove_from_pinboard()

    def update_option_pin_x(self):
        """Called when the pin_x option has changed."""
        self.remove_from_pinboard()
        self.add_to_pinboard()

    def update_option_pin_y(self):
        """Called when the pin_y option has changed."""
        self.remove_from_pinboard()
        self.add_to_pinboard()


    # Signal handlers

    def __removed(self, volume, mount=None):
        for window in self.windows:
            window.close(0)
        self.remove_from_pinboard(mount)

    def __drag_data_get(self, widget, context, data, info, time):
        if not self.visible_windows:
            return
        if info == TARGET_WNCK_WINDOW_ID:
            xid = self.visible_windows[0].get_xid()
            data.set(data.target, 8, apply(struct.pack, ['1i', xid]))
        else:
            mount = self.__volume.get_mount()
            if mount is None:
                return
            root = mount.get_root()
            if root is None:
                return
            data.set_uris([root.get_uri()])

    def mounted(self):
        mount = self.__volume.get_mount()
        self.update_icon()
        self.update_emblem()
        self.__set_icon(self.get_icon_path())
        self.add_to_pinboard()

    def unmounted(self, mount):
        self.update_emblem()
        self.__removed(self.__volume, mount)


    # Pinboard

    def add_to_pinboard(self):
        """
        Add the volume to the pinboard.

        Only works if the volume is mounted and the pin option is set.
        """
        if self.__is_on_pinboard:
            return
        if not self.mediaicon_config.pin:
            return
        root_path = self.mountpoint
        if root_path is None:
            return
        f = os.popen('rox --RPC', 'w')
        rpc = (
            '<?xml version="1.0"?>'
            '<env:Envelope xmlns:env="http://www.w3.org/2001/12/soap-envelope">'
                '<env:Body xmlns="http://rox.sourceforge.net/SOAP/ROX-Filer">'
                    '<PinboardAdd>'
                        '<Path>' + escape(root_path) + '</Path>'
                        '<Label>' + escape(self.name) + '</Label>'
                        '<X>' + str(self.mediaicon_config.pin_x) + '</X>'
                        '<Y>' + str(self.mediaicon_config.pin_y) + '</Y>'
                        '<Update>1</Update>'
                    '</PinboardAdd>'
                '</env:Body>'
            '</env:Envelope>')
        f.write(rpc)
        f.close()
        if root_path not in volumes_on_pinboard:
            volumes_on_pinboard.append(root_path)
            f = open(_volumes_on_pinboard_path, 'w')
            try:
                json.dump(volumes_on_pinboard, f)
            finally:
                f.close()
        self.__is_on_pinboard = True

    def remove_from_pinboard(self, mount=None, unset_icon=False):
        """Remove the volume from the pinboard."""
        if mount is None:
            mount = self.__volume.get_mount()
        if mount is None:
            return
        if not self.__is_on_pinboard:
            return
        root = mount.get_root()
        if root is None:
            return
        root_path = root.get_path()
        if not root_path:
            return
        f = os.popen('rox --RPC', 'w')
        tmp = (
            '<?xml version="1.0"?>'
            '<env:Envelope xmlns:env="http://www.w3.org/2001/12/soap-envelope">'
                '<env:Body xmlns="http://rox.sourceforge.net/SOAP/ROX-Filer">'
                    '<PinboardRemove>'
                        '<Path>' + escape(root_path) + '</Path>'
                    '</PinboardRemove>'
        )
        if unset_icon:
            tmp += (
                    '<UnsetIcon>'
                        '<Path>' + escape(root_path) + '</Path>'
                    '</UnsetIcon>'
            )
        tmp += (
                '</env:Body>'
            '</env:Envelope>'
        )
        f.write(tmp)
        f.close()
        if root_path in volumes_on_pinboard:
            volumes_on_pinboard.remove(root_path)
            f = open(_volumes_on_pinboard_path, 'w')
            try:
                json.dump(volumes_on_pinboard, f)
            finally:
                f.close()
        self.__is_on_pinboard = False


    # Icon handling

    def __set_icon(self, icon_path):
        if icon_path is None:
            return
        root_path = self.mountpoint
        if root_path is None:
            return
        f = os.popen('rox --RPC', 'w')
        f.write(
            '<?xml version="1.0"?>'
            '<env:Envelope xmlns:env="http://www.w3.org/2001/12/soap-envelope">'
                '<env:Body xmlns="http://rox.sourceforge.net/SOAP/ROX-Filer">'
                    '<SetIcon>'
                        '<Path>' + escape(root_path) + '</Path>'
                        '<Icon>' + escape(icon_path) + '</Icon>'
                    '</SetIcon>'
                '</env:Body>'
            '</env:Envelope>'
        )
        f.close()

    def get_individual_icon_path(self):
        root_path = self.mountpoint
        if root_path is None:
            return None

        # Try to read diricon.
        icon_path = os.path.join(root_path, '.DirIcon')
        if os.access(icon_path, os.R_OK):
            return icon_path

        # Try to read icon from windows autorun.
        windows_autorun = self.__read_windows_autorun()
        if windows_autorun is not None and windows_autorun.icon is not None:
            icon_path = get_case_sensitive_path(
                os.path.join(root_path, windows_autorun.icon), root_path
            )
            if os.access(icon_path, os.R_OK):
                return icon_path

        return None

    def get_fallback_icon_path():
        return os.path.join(rox.app_dir, 'icons', 'drive-harddisk.png')

    
    # Windows autorun support

    def __read_windows_autorun(self):
        root_path = self.mountpoint
        if root_path is None:
            return None

        path = os.path.join(root_path, 'autorun.inf')
        parser = RawConfigParser()

        if parser.read(path) != [path]:
            return

        windows_autorun = WindowsAutoRun()

        for section in parser.sections():
            if section.lower() == SECTION_WINDOWS_AUTORUN:
                break
        else:
            return None

        try:
            icon = parser.get(section, "icon")
        except NoOptionError:
            pass # no icon
           
        try:
            exe = parser.get(section, "open")
        except NoOptionError:
            exe = None # no exe
        
        windows_autorun = WindowsAutoRun()
        if icon and '..' not in icon:
            windows_autorun.icon = icon
        if '..' not in exe:
            windows_autorun.exe = exe
        return windows_autorun


    # Methods overridden from WinIcon.

    def should_hide_if_no_visible_windows(self):
        return False

    def should_have_window(self, window):
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
        return False


    # Methods overridden from Icon.

    def get_icon_path(self):
        icon_path = self.get_individual_icon_path()
        if icon_path is not None:
            return icon_path

        icon_names = self.icon_names
        for icon_name in icon_names:
            icon_info = ICON_THEME.lookup_icon(icon_name, 48, 0)
            if icon_info is not None:
                icon_path = icon_info.get_filename()
                #icon_info.free()
                break
        else:
            icon_path = self.get_fallback_icon_path()
        return icon_path

    def get_menu_right(self):
        menu = WinIcon.get_menu_right(self)
        if not menu:
            menu = gtk.Menu()
        else:
            menu.prepend(gtk.SeparatorMenuItem())
            menu.prepend(gtk.SeparatorMenuItem())

        if self.__volume.can_eject():
            eject_item = gtk.ImageMenuItem(_("Eject"))
            eject_image = gtk.image_new_from_pixbuf(
                ICON_THEME.load_icon("media-eject", gtk.ICON_SIZE_MENU, 0)
            )
            eject_item.set_image(eject_image)
            eject_item.set_use_stock(False)
            eject_item.connect("activate", lambda item: self.eject()) 
            menu.prepend(eject_item)

        if self.__volume.can_mount():
            if self.__volume.get_mount():
                unmount_item = gtk.ImageMenuItem(gtk.STOCK_CANCEL)
                unmount_item.set_label(_("Unmount"))
                unmount_item.connect("activate", lambda item: self.unmount()) 
                menu.prepend(unmount_item)
            else:
                mount_item = gtk.ImageMenuItem(gtk.STOCK_YES)
                mount_item.set_label(_("Mount"))
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
        if WinIcon.click(self):
            return True
        self.open()
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
                self.copy(uri_list)
            elif action == gtk.gdk.ACTION_MOVE:
                self.copy(uri_list, True)
        else:
            if action == gtk.gdk.ACTION_COPY:
                self.mount(on_mount=partial(
                    self.copy, uri_list=uri_list, move=False
                ))
            elif action == gtk.gdk.ACTION_MOVE:
                self.mount(on_mount=partial(
                    self.copy, uri_list=uri_list, move=True
                ))

    def spring_open(self, time = 0L):
        if WinIcon.spring_open(self, time):
            return True
        self.open()
        return False

    mediaicon_config = property(lambda self : self.__mediaicon_config)
