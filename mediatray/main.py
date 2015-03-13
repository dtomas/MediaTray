import rox
from rox.options import Option

from traylib.main import Main
from traylib.winicon import WinIconConfig

from mediatray import MediaTray


class MediaTrayMain(Main):
    
    def __init__(self):
        Main.__init__(self, "MediaTray")

    def init_options(self):
        Main.init_options(self)
        self.__o_all_workspaces = Option("all_workspaces", False)
        self.__o_arrow = Option("arrow", True)
 
    def init_config(self):
        Main.init_config(self)
        self.__win_config = WinIconConfig(self.__o_all_workspaces.int_value, 
                                          self.__o_arrow.int_value)

        # MediaTray doesn't use the 'hidden' option, so make sure no icons get
        # hidden.
        self.icon_config.hidden = False

    def mainloop(self, app_args):
        Main.mainloop(self, app_args, MediaTray, self.__win_config)

    def options_changed(self):
        if self.__o_arrow.has_changed:
            self.__win_config.arrow = self.__o_arrow.int_value
    
        if self.__o_all_workspaces.has_changed:
            self.__win_config.all_workspaces = self.__o_all_workspaces.int_value

        Main.options_changed(self)

    win_config = property(lambda self : self.__win_config)
