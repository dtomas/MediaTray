import gio

from mediatray.mediaicon import MediaIcon

from mediatray.mounticon_config import NO_AUTOMOUNT, AUTOMOUNT, AUTOOPEN


def manage_mediaicons(tray, screen, icon_config, win_config, mounticon_config):
    """
    Manages a L{mediatray.MediaTray}.

    @param tray: The tray to manage.
    @param screen: The C{wnck.Screen} or C{None} to disable showing open
        windows in icon menus.
    @param icon_config: The config for C{Icon}s.
    @param win_config: The config for C{WinIcon}s.
    @param mounticon_config: The config for C{MountIcon}s.

    @return: manage, unmanage: functions to start/stop managing the tray.
    """

    volume_monitor = gio.volume_monitor_get()

    automount_actions = {
        NO_AUTOMOUNT: lambda icon: None,
        AUTOMOUNT: MediaIcon.mount,
        AUTOOPEN: MediaIcon.open,
    }

    tray.add_box(None)

    def volume_added(volume_monitor, volume, initial=False):
        icon = MediaIcon(icon_config, win_config, mounticon_config, volume,
                         screen)
        tray.add_icon(None, volume, icon)
        if not initial:
            automount_actions[mounticon_config.automount](icon)

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
            volume_added(volume_monitor, volume, initial=True)
            yield None

    def unmanage():
        volume_monitor.disconnect(handlers.volume_added_handler)
        volume_monitor.disconnect(handlers.volume_removed_handler)
        yield None

    return manage, unmanage
