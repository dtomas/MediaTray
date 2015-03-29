from functools import partial

import gobject

from rox import tasks

from traylib import *
from traylib.managed_tray import ManagedTray
from traylib.winicon_manager import manage_winicons

from mediatray.main_icon import MainIcon
from mediatray.mounticon import MountIcon
from mediatray.mediaicon_manager import manage_mediaicons
from mediatray.hosticon_manager import manage_hosticons
from mediatray.notification_manager import manage_notifications
from mediatray.pinboard_manager import manage_pinboard
from mediatray.automount_manager import manage_automount


class MediaTray(ManagedTray):
    """
    Tray containing L{mediatray.mediaicon.MediaIcon}s.
    Managed by L{mediatray.mediaicon_manager.manage_mediaicons}.
    """

    def __init__(self, icon_config, tray_config, win_config, pinboard_config,
                 notification_config, automount_config, screen, host_manager,
                 volume_monitor):
        self.__win_config = win_config
        self.__screen = screen
        self.__icon_handlers = {}
        ManagedTray.__init__(
            self, icon_config, tray_config,
            create_menu_icon=partial(
                MainIcon, win_config=win_config, host_manager=host_manager
            ),
            managers=[
                partial(
                    manage_pinboard,
                    pinboard_config=pinboard_config,
                ),
                partial(
                    manage_mediaicons,
                    screen=screen,
                    icon_config=icon_config,
                    win_config=win_config,
                    volume_monitor=volume_monitor,
                ),
                partial(
                    manage_hosticons,
                    screen=screen,
                    icon_config=icon_config,
                    win_config=win_config,
                    host_manager=host_manager,
                    volume_monitor=volume_monitor,
                ),
                partial(
                    manage_automount,
                    automount_config=automount_config,
                ),
                partial(
                    manage_notifications,
                    notification_config=notification_config,
                ),
                partial(manage_winicons, screen=screen),
            ],
        )

    def add_icon(self, box_id, icon_id, icon):
        ManagedTray.add_icon(self, box_id, icon_id, icon)
        self.__icon_handlers[icon_id] = (
            icon.connect(
                "mounted", lambda icon: self.emit("icon-mounted", icon)
            ),
            icon.connect(
                "unmounted", lambda icon: self.emit("icon-unmounted", icon)
            )
        )

    def remove_icon(self, icon_id):
        icon = self.get_icon(icon_id)
        if icon is None:
            return
        ManagedTray.remove_icon(self, icon_id)
        for handler in self.__icon_handlers.pop(icon_id):
            icon.disconnect(handler)

    win_config = property(lambda self : self.__win_config)

gobject.type_register(MediaTray)
gobject.signal_new(
    "icon-mounted", MediaTray, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
    (MountIcon,)
)
gobject.signal_new(
    "icon-unmounted", MediaTray, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
    (MountIcon,)
)
