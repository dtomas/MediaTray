from functools import partial

from rox import tasks

from traylib import *
from traylib.managed_tray import ManagedTray
from traylib.winicon_manager import manage_winicons

from mediatray.main_icon import MainIcon
from mediatray.mounticon_manager import manage_mounticons
from mediatray.mediaicon_manager import manage_mediaicons
from mediatray.hosticon_manager import manage_hosticons


class MediaTray(ManagedTray):
    """
    Tray containing L{mediatray.mediaicon.MediaIcon}s.
    Managed by L{mediatray.mediaicon_manager.manage_mediaicons}.
    """

    def __init__(self, icon_config, tray_config, win_config, mounticon_config,
                 screen, host_manager):
        self.__win_config = win_config
        self.__mounticon_config = mounticon_config
        self.__screen = screen
        ManagedTray.__init__(
            self, icon_config, tray_config,
            create_menu_icon=partial(
                MainIcon, win_config=win_config, host_manager=host_manager
            ),
            managers=[
                partial(
                    manage_mounticons,
                    mounticon_config=mounticon_config,
                ),
                partial(
                    manage_mediaicons,
                    screen=screen,
                    icon_config=icon_config,
                    win_config=win_config,
                    mounticon_config=mounticon_config,
                ),
                partial(
                    manage_hosticons,
                    screen=screen,
                    icon_config=icon_config,
                    win_config=win_config,
                    mounticon_config=mounticon_config,
                    host_manager=host_manager,
                ),
                partial(manage_winicons, screen=screen),
            ],
        )

    win_config = property(lambda self : self.__win_config)
    mounticon_config = property(lambda self : self.__mounticon_config)
