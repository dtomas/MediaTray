from functools import partial

from rox import tasks

from traylib import *
from traylib.managed_tray import ManagedTray
from traylib.winicon_manager import manage_winicons

from mediatray.main_icon import MainIcon
from mediatray.mediaicon_manager import manage_mediaicons


class MediaTray(ManagedTray):
    """
    Tray containing L{mediatray.mediaicon.MediaIcon}s.
    Managed by L{mediatray.mediaicon_manager.manage_mediaicons}.
    """

    def __init__(self, icon_config, tray_config, win_config, mediaicon_config,
                 screen):
        self.__win_config = win_config
        self.__mediaicon_config = mediaicon_config
        self.__screen = screen
        ManagedTray.__init__(
            self, icon_config, tray_config,
            create_menu_icon=partial(MainIcon, win_config=win_config),
            managers=[
                partial(
                    manage_mediaicons,
                    screen=screen,
                    icon_config=icon_config,
                    win_config=win_config,
                    mediaicon_config=mediaicon_config,
                ),
                partial(manage_winicons, screen=screen),
            ],
        )

    win_config = property(lambda self : self.__win_config)
    mediaicon_config = property(lambda self : self.__mediaicon_config)
