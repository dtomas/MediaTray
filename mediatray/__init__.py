from rox import tasks

from traylib import *
from traylib.tray import Tray

from mediatray.main_icon import MainIcon
from mediatray.mediaicon_manager import MediaIconManager


class MediaTray(Tray):

    def __init__(self, icon_config, tray_config, win_config):
        self.__win_config = win_config
        Tray.__init__(self, icon_config, tray_config, MainIcon)

        self.add_box(None)

        self.__icon_manager = MediaIconManager(
            self, SCREEN, icon_config, win_config
        )
        tasks.Task(self.__icon_manager.init())

    def quit(self):
        tasks.Task(self.__icon_manager.quit())

    win_config = property(lambda self : self.__win_config)
