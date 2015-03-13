import gio

from traylib.winicon_manager import WinIconManager

from mediatray.mediaicon import MediaIcon


class MediaIconManager(WinIconManager):

    def __init__(self, tray, screen, icon_config, win_config):
        WinIconManager.__init__(self, tray, screen)
        self.__icon_config = icon_config
        self.__win_config = win_config

    def init(self):
        self.__volume_monitor = gio.volume_monitor_get()

        for volume in self.__volume_monitor.get_volumes():
            if not volume.get_drive().is_media_removable():
                continue
            icon = MediaIcon(self.__icon_config, self.__win_config, volume)
            self.tray.add_icon(None, volume.get_uuid(), icon)
            self.icon_added(icon)
            yield None

        for x in WinIconManager.init(self):
            yield x

        self.__volume_monitor.connect("volume-added", self.__volume_added)
        self.__volume_monitor.connect("volume-removed", self.__volume_removed)

    def __volume_added(self, volume_monitor, volume):
        icon = MediaIcon(self.icon_config, self.__win_config, volume)
        self.tray.add_icon(None, volume.get_uuid(), icon)
        self.icon_added(icon)

    def __volume_removed(self, volume_monitor, volume):
        self.tray.remove_icon(volume.get_uuid())

    icon_config = property(lambda self : self.__icon_config)
    win_config = property(lambda self : self.__win_config)
