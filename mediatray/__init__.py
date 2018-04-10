from functools import partial

from gi.repository import GObject

from traylib import *
from traylib.managed_tray import ManagedTray
from traylib.main_box_manager import manage_main_box

from mediatray.main_item import MediaTrayMainItem
from mediatray.mountitem import MountItem
from mediatray.mediaitem_manager import manage_mediaitems
from mediatray.hostitem_manager import manage_hostitems
from mediatray.notification_manager import manage_notifications
from mediatray.pinboard_manager import manage_pinboard
from mediatray.automount_manager import manage_automount
from mediatray.winitem_manager import manage_winitems


class MediaTray(ManagedTray):

    def __init__(self, tray_config, icon_config, win_config, pinboard_config,
                 notification_config, automount_config, mediaitem_config,
                 screen, host_manager, volume_monitor):
        self.__win_config = win_config
        self.__screen = screen
        ManagedTray.__init__(
            self,
            managers=[
                partial(
                    manage_pinboard,
                    pinboard_config=pinboard_config,
                ),
                partial(
                    manage_mediaitems,
                    screen=screen,
                    win_config=win_config,
                    mediaitem_config=mediaitem_config,
                    volume_monitor=volume_monitor,
                ),
                #partial(
                #    manage_hostitems,
                #    screen=screen,
                #    win_config=win_config,
                #    host_manager=host_manager,
                #    volume_monitor=volume_monitor,
                #),
                partial(
                    manage_automount,
                    automount_config=automount_config,
                ),
                partial(
                    manage_notifications,
                    notification_config=notification_config,
                ),
                partial(manage_winitems, screen=screen, win_config=win_config),
                partial(
                    manage_main_box,
                    tray_config=tray_config,
                    create_main_item=partial(
                        MediaTrayMainItem,
                        tray_config=tray_config,
                        icon_config=icon_config,
                        win_config=win_config,
                        mediaitem_config=mediaitem_config,
                        host_manager=host_manager,
                    ),
                ),
            ],
        )
        self.__item_handlers = {}

        self.connect("item-added", self.__item_added)
        self.connect("item-removed", self.__item_removed)

    def __item_added(self, tray, box, item):
        if not isinstance(item, MountItem):
            return
        self.__item_handlers[item] = [
            item.connect("mounted", self.__item_mounted),
            item.connect("unmounted", self.__item_unmounted),
        ]
    
    def __item_removed(self, tray, box, item):
        if not isinstance(item, MountItem):
            return
        for handler in self.__item_handlers.pop(item):
            item.disconnect(handler)

    def __item_mounted(self, item):
        self.emit("item-mounted", item)

    def __item_unmounted(self, item):
        self.emit("item-unmounted", item)

    win_config = property(lambda self : self.__win_config)

GObject.type_register(MediaTray)
GObject.signal_new(
    "item-mounted", MediaTray, GObject.SignalFlags.RUN_FIRST, None,
    (MountItem,)
)
GObject.signal_new(
    "item-unmounted", MediaTray, GObject.SignalFlags.RUN_FIRST, None,
    (MountItem,)
)
