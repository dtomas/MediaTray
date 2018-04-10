from traylib.item_box import ItemBox

from mediatray.mediaitem import MediaItem


def manage_mediaitems(tray, screen, win_config, mediaitem_config,
                      volume_monitor):
    """
    Manages a L{mediatray.MediaTray}.

    @param tray: The tray to manage.
    @param screen: The C{Wnck.Screen} or C{None} to disable showing open
        windows in icon menus.
    @param win_config: The config for C{WinIcon}s.

    @return: manage, unmanage: functions to start/stop managing the tray.
    """

    class state:
        handlers = []
        box = None

    def volume_added(volume_monitor, volume):
        state.box.add_item(
            MediaItem(
                win_config, mediaitem_config, volume, screen, volume_monitor
            ),
        )

    def manage():
        state.box = ItemBox("mediaitems")
        tray.add_box(state.box)
        state.handlers = [volume_monitor.connect("volume-added", volume_added)]
        for volume in volume_monitor.get_volumes():
            volume_added(volume_monitor, volume)
            yield None

    def unmanage():
        for handler in state.handlers:
            volume_monitor.disconnect(handler)
            yield None
        state.handlers = []
        tray.remove_box(state.box)
        state.box = None

    return manage, unmanage
