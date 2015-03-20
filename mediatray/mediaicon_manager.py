import gio

from mediatray.mediaicon import MediaIcon
from mediatray.mediaicon_config import AUTOMOUNT, AUTOOPEN


def manage_mediaicons(tray, screen, icon_config, win_config, mediaicon_config):

    volume_monitor = gio.volume_monitor_get()

    automount_actions = {
        0: lambda: None,
        1: MediaIcon.mount,
        2: MediaIcon.open,
    }

    tray.add_box(None)

    def volume_added(volume_monitor, volume, initial=False):
        icon = MediaIcon(icon_config, win_config, mediaicon_config, volume,
                         screen)
        tray.add_icon(None, volume, icon)
        if not initial:
            automount_actions[mediaicon_config.automount](icon)

    def volume_removed(self, volume_monitor, volume):
        tray.remove_icon(volume)

    volume_added_handler = volume_monitor.connect("volume-added",
                                                  volume_added)
    volume_removed_handler = volume_monitor.connect("volume-removed",
                                                    volume_removed)

    def manage():
        for volume in volume_monitor.get_volumes():
            volume_added(volume_monitor, volume, initial=True)
            yield None

    def unmanage():
        volume_monitor.disconnect(volume_added_handler)
        volume_monitor.disconnect(volume_removed_handler)
        yield None

    return manage, unmanage
