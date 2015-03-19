import gio

from traylib.winicon_manager import WinIconManager

from mediatray.mediaicon import MediaIcon
from mediatray.mediaicon_config import AUTOMOUNT, AUTOOPEN


class MediaIconManager(WinIconManager):

    def __init__(self, tray, screen, icon_config, win_config,
                 mediaicon_config):
        WinIconManager.__init__(self, tray, screen)
        self.__icon_config = icon_config
        self.__win_config = win_config
        self.__mediaicon_config = mediaicon_config
        self.__automount_actions = {
            0: lambda: None,
            1: MediaIcon.mount,
            2: MediaIcon.open,
        }

    def init(self):
        self.__volume_monitor = gio.volume_monitor_get()

        for volume in self.__volume_monitor.get_volumes():
            self.__volume_added(self.__volume_monitor, volume, initial=True)
            yield None

        for x in WinIconManager.init(self):
            yield x

        self.__volume_monitor.connect("volume-added", self.__volume_added)
        self.__volume_monitor.connect("volume-removed", self.__volume_removed)

    def __volume_added(self, volume_monitor, volume, initial=False):
        icon = MediaIcon(self.icon_config, self.__win_config,
                         self.__mediaicon_config, volume, self.screen)
        self.tray.add_icon(None, volume, icon)
        if not initial:
            self.__automount_actions[self.mediaicon_config.automount](icon)
        self.icon_added(icon)

    def __volume_removed(self, volume_monitor, volume):
        self.tray.remove_icon(volume)

    icon_config = property(lambda self : self.__icon_config)
    win_config = property(lambda self : self.__win_config)
    mediaicon_config = property(lambda self : self.__mediaicon_config)

