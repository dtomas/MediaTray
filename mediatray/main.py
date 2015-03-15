import rox
from rox.options import Option

from traylib.main import Main
from traylib.winicon import WinIconConfig

from mediatray import MediaTray
from mediatray.config import PROJECT, SITE
from mediatray.mediaicon_config import MediaIconConfig, PIN_LEFT, PIN_TOP


class MediaTrayMain(Main):
    
    def __init__(self):
        Main.__init__(self, "MediaTray")

    def init_options(self):
        Main.init_options(self)
        self.__o_all_workspaces = Option("all_workspaces", False)
        self.__o_arrow = Option("arrow", True)
        self.__o_pin = Option("pin", True)
        self.__o_pin_x = Option("pin_x", PIN_LEFT)
        self.__o_pin_y = Option("pin_y", PIN_TOP)
 
    def init_config(self):
        Main.init_config(self)
        self.__win_config = WinIconConfig(self.__o_all_workspaces.int_value, 
                                          self.__o_arrow.int_value)
        self.__mediaicon_config = MediaIconConfig(self.__o_pin.int_value,
                                                  self.__o_pin_x.int_value,
                                                  self.__o_pin_y.int_value)

        # MediaTray doesn't use the 'hidden' option, so make sure no icons get
        # hidden.
        self.icon_config.hidden = False

    def mainloop(self, app_args):
        Main.mainloop(self, app_args, MediaTray, self.__win_config,
                      self.__mediaicon_config)

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

        Main.options_changed(self)

    win_config = property(lambda self : self.__win_config)
