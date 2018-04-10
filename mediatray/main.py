import gi
from gi.repository import Gio
try:
    gi.require_version('Wnck', '3.0')
    from gi.repository import Wnck
except ImportError:
    Wnck = None

from rox.options import Option

from traylib.main import Main
from traylib.winitem_config import WinItemConfig

from mediatray import MediaTray
from mediatray.pinboard_config import PinboardConfig, PIN_LEFT, PIN_TOP
from mediatray.automount_config import AutomountConfig, AUTOMOUNT
from mediatray.notification_config import NotificationConfig
from mediatray.mediaitem_config import MediaItemConfig
from mediatray.host_manager import HostManager


class MediaTrayMain(Main):
    
    def __init__(self):
        Main.__init__(self, "MediaTray")
        self.__screen = Wnck.Screen.get_default() if Wnck is not None else None

    def init_options(self):
        Main.init_options(self)
        self.__o_all_workspaces = Option("all_workspaces", False)
        self.__o_arrow = Option("arrow", True)
        self.__o_pin = Option("pin", True)
        self.__o_pin_x = Option("pin_x", PIN_LEFT)
        self.__o_pin_y = Option("pin_y", PIN_TOP)
        self.__o_automount = Option("automount", AUTOMOUNT)
        self.__o_show_notifications = Option("show_notifications", True)
        self.__o_hide_unmounted = Option("hide_unmounted", True)
 
    def init_config(self):
        Main.init_config(self)
        self.__win_config = WinItemConfig(
            all_workspaces=self.__o_all_workspaces.int_value,
            arrow=self.__o_arrow.int_value,
        )
        self.__pinboard_config = PinboardConfig(
            pin=self.__o_pin.int_value,
            pin_x=self.__o_pin_x.int_value,
            pin_y=self.__o_pin_y.int_value,
        )
        self.__automount_config = AutomountConfig(
            automount=self.__o_automount.int_value,
        )
        self.__notification_config = NotificationConfig(
            show_notifications=bool(self.__o_show_notifications.int_value),
        )
        self.__mediaitem_config = MediaItemConfig(
            hide_unmounted=bool(self.__o_hide_unmounted.int_value),
        )

        # MediaTray doesn't use the 'hidden' option, so make sure no icons get
        # hidden.
        self.icon_config.hidden = False

        self.__win_config.menu_has_kill = False

    def create_tray(self):
        return MediaTray(
            tray_config=self.tray_config,
            icon_config=self.icon_config,
            win_config=self.__win_config,
            pinboard_config=self.__pinboard_config,
            automount_config=self.__automount_config,
            notification_config=self.__notification_config,
            mediaitem_config=self.__mediaitem_config,
            screen=self.__screen,
            host_manager=HostManager(),
            volume_monitor=Gio.VolumeMonitor.get(),
        )

    def options_changed(self):
        if self.__o_arrow.has_changed:
            self.__win_config.arrow = self.__o_arrow.int_value
    
        if self.__o_all_workspaces.has_changed:
            self.__win_config.all_workspaces = bool(
                self.__o_all_workspaces.int_value
            )

        if self.__o_pin.has_changed:
            self.__pinboard_config.pin = self.__o_pin.int_value

        if self.__o_pin_x.has_changed:
            self.__pinboard_config.pin_x = self.__o_pin_x.int_value

        if self.__o_pin_y.has_changed:
            self.__pinboard_config.pin_y = self.__o_pin_y.int_value

        if self.__o_automount.has_changed:
            self.__automount_config.automount = self.__o_automount.int_value

        if self.__o_show_notifications.has_changed:
            self.__notification_config.show_notifications = bool(
                self.__o_show_notifications.int_value
            )

        if self.__o_hide_unmounted.has_changed:
            self.__mediaitem_config.hide_unmounted = bool(
                self.__o_hide_unmounted.int_value
            )

        Main.options_changed(self)
