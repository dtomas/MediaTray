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

    def volume_removed(volume_monitor, volume):
        tray.remove_icon(volume)

    def mount_added(volume, mount):
        for icon in tray.icons:
            icon.mounted()

    def mount_removed(volume, mount):
        for icon in tray.icons:
            icon.unmounted(mount)

    class handlers:
        pass

    def manage():
        handlers.volume_added_handler = volume_monitor.connect("volume-added",
                                                               volume_added)
        handlers.volume_removed_handler = (
            volume_monitor.connect("volume-removed", volume_removed)
        )
        handlers.mount_added_handler = volume_monitor.connect("mount-added",
                                                              mount_added)
        handlers.mount_removed_handler = (
            volume_monitor.connect("mount-removed", mount_removed)
        )
        for volume in volume_monitor.get_volumes():
            volume_added(volume_monitor, volume, initial=True)
            yield None

    def unmanage():
        volume_monitor.disconnect(handlers.volume_added_handler)
        volume_monitor.disconnect(handlers.volume_removed_handler)
        volume_monitor.disconnect(handlers.mount_added_handler)
        volume_monitor.disconnect(handlers.mount_removed_handler)
        for icon in tray.icons:
            icon.remove_from_pinboard()
        yield None

    return manage, unmanage
