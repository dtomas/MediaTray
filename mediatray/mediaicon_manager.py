from rox import processes

from mediatray.mediaicon import MediaIcon


def manage_mediaicons(tray, screen, icon_config, win_config, mediaicon_config,
                      volume_monitor):
    """
    Manages a L{mediatray.MediaTray}.

    @param tray: The tray to manage.
    @param screen: The C{wnck.Screen} or C{None} to disable showing open
        windows in icon menus.
    @param icon_config: The config for C{Icon}s.
    @param win_config: The config for C{WinIcon}s.

    @return: manage, unmanage: functions to start/stop managing the tray.
    """


    tray.add_box(None)

    def volume_added(volume_monitor, volume):
        tray.add_icon(
            None, volume,
            MediaIcon(icon_config, win_config, mediaicon_config, volume,
                      screen, volume_monitor),
        )

    def volume_removed(volume_monitor, volume):
        tray.remove_icon(volume)

    class handlers:
        pass

    def manage():
        handlers.volume_added_handler = volume_monitor.connect("volume-added",
                                                               volume_added)
        handlers.volume_removed_handler = (
            volume_monitor.connect("volume-removed", volume_removed)
        )
        for volume in volume_monitor.get_volumes():
            volume_added(volume_monitor, volume)
            yield None

    def unmanage():
        volume_monitor.disconnect(handlers.volume_added_handler)
        volume_monitor.disconnect(handlers.volume_removed_handler)
        yield None

    return manage, unmanage
