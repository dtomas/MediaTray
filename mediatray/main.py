from functools import partial

import rox
from rox.options import Option

from traylib import wnck
from traylib.main import Main
from traylib.winicon import WinIconConfig

from mediatray import MediaTray
from mediatray.mediaicon_config import MediaIconConfig, PIN_LEFT, PIN_TOP


class MediaTrayMain(Main):
    
    def __init__(self):
        Main.__init__(self, "MediaTray")
        self.__screen = wnck.screen_get_default() if wnck is not None else None

    def init_options(self):
        Main.init_options(self)
        self.__o_all_workspaces = Option("all_workspaces", False)
        self.__o_arrow = Option("arrow", True)
        self.__o_pin = Option("pin", True)
        self.__o_pin_x = Option("pin_x", PIN_LEFT)
        self.__o_pin_y = Option("pin_y", PIN_TOP)
        self.__o_automount = Option("automount", 0)
        self.__o_show_notifications = Option("show_notifications", True)
 
    def init_config(self):
        Main.init_config(self)
        self.__win_config = WinIconConfig(
            all_workspaces=self.__o_all_workspaces.int_value,
            arrow=self.__o_arrow.int_value,
        )
        self.__mediaicon_config = MediaIconConfig(
            pin=self.__o_pin.int_value,
            pin_x=self.__o_pin_x.int_value,
            pin_y=self.__o_pin_y.int_value,
            automount=self.__o_automount.int_value,
            show_notifications=self.__o_show_notifications,
        )

        # MediaTray doesn't use the 'hidden' option, so make sure no icons get
        # hidden.
        self.icon_config.hidden = False

    def mainloop(self, app_args):
        Main.mainloop(
            self, app_args,
            partial(
                MediaTray,
                win_config=self.__win_config,
                mediaicon_config=self.__mediaicon_config,
                screen=self.__screen
            )
        )

    def options_changed(self):
        if self.__o_arrow.has_changed:
            self.__win_config.arrow = self.__o_arrow.int_value
    
        if self.__o_all_workspaces.has_changed:
            self.__win_config.all_workspaces = bool(
                self.__o_all_workspaces.int_value
            )

        if self.__o_pin.has_changed:
            self.__mediaicon_config.pin = self.__o_pin.int_value

        if self.__o_pin_x.has_changed:
            self.__mediaicon_config.pin_x = self.__o_pin_x.int_value

        if self.__o_pin_y.has_changed:
            self.__mediaicon_config.pin_y = self.__o_pin_y.int_value

        if self.__o_automount.has_changed:
            self.__mediaicon_config.automount = self.__o_automount.int_value

        if self.__o_show_notifications.has_changed:
            self.__mounticon_config.show_notifications = bool(
                self.__o_show_notifications.int_value
            )

        Main.options_changed(self)
