import os
from ConfigParser import RawConfigParser, NoOptionError

import gtk

import gio

import rox
from rox import filer

from traylib import ICON_THEME

from mediatray.mounticon import MountIcon


SECTION_WINDOWS_AUTORUN = 'autorun'


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


class MediaIcon(MountIcon):

    def __init__(self, icon_config, win_config, mediaicon_config, volume,
                 screen, volume_monitor):
        self.__mediaicon_config = mediaicon_config
        mediaicon_config.add_configurable(self)
        self.__volume = volume
        MountIcon.__init__(self, icon_config, win_config, screen,
                           volume_monitor)

        self.mount_label = _("Mount")
        self.unmount_label = _("Unmount")
        self.__volume.connect("removed", lambda volume: self.__removed())
        self.connect("unmounted", lambda self: self.update_visibility())
        self.connect("mounted", lambda self: self.update_visibility())

        mount = self.__volume.get_mount()

    def get_mount(self):
        return self.__volume.get_mount()

    def make_path(self):
        """The volume's mount point or C{None} if the volume is not mounted."""
        mount = self.__volume.get_mount()
        if mount is None:
            return None
        root = mount.get_root()
        if root is None:
            # Should never happen, but anyway...
            return None
        return root.get_path()


    # Methods invoked when a MediaIconConfig attribute has changed

    def update_option_hide_unmounted(self):
        self.update_visibility()


    # Signal handlers

    def __removed(self):
        for window in self.windows:
            window.close(0)


    # Actions

    def _mount(self, on_mount=None):
        """
        Mount the volume.

        @param on_mount: function which gets called with the volume's
            C{gio.Mount} object when the volume has been mounted.
        """
        def mounted(volume, result):
            if not volume.mount_finish(result):
                return
            mount = volume.get_mount()
            if on_mount is not None:
                on_mount()
        self.__volume.mount(gtk.MountOperation(), mounted)

    def eject(self):
        """Eject the volume."""
        def ejected(volume, result):
            self.__volume.eject_finish(result)
        self.__volume.eject(ejected)


    # Icon handling

    def get_individual_icon_path(self):
        """
        Get the path of the .DirIcon or an icon defined in Windows'
        autorun.inf.
        """
        icon_path = MountIcon.get_individual_icon_path(self)
        if icon_path is not None:
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
        """Read path to icon and executable from Windows' autorun.inf."""
        path = self.path
        if path is None:
            return None

        autorun_path = os.path.join(path, 'autorun.inf')
        parser = RawConfigParser()

        if parser.read(autorun_path) != [path]:
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


    # Methods overridden from Icon.

    def get_menu_right(self):
        menu = MountIcon.get_menu_right(self)

        if self.__volume.can_eject():
            eject_item = gtk.ImageMenuItem(_("Eject"))
            eject_image = gtk.image_new_from_pixbuf(
                ICON_THEME.load_icon("media-eject", gtk.ICON_SIZE_MENU, 0)
            )
            eject_item.set_image(eject_image)
            eject_item.set_use_stock(False)
            eject_item.connect("activate", lambda item: self.eject()) 
            menu.insert(eject_item, 3)

        return menu

    def get_icon_names(self):
        """Get the icon names for the volume."""
        # Fallback icon, shipped with MediaTray.
        icons = ["drive-harddisk"]
        icon = self.__volume.get_icon()
        if icon is not None and hasattr(icon, 'get_names'):
            icons = icon.get_names() + icons
        return icons

    def make_name(self):
        """Return the name of the volume."""
        return self.__volume.get_name()

    def make_visibility(self):
        return self.is_mounted or not self.__mediaicon_config.hide_unmounted

    volume = property(lambda self : self.__volume)
    """The underlying C{gio.Volume} object."""
