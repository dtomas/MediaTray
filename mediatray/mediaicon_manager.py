import gio

from rox import processes

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

    mount2icon = {}

    tray.add_box(None)

    def volume_added(volume_monitor, volume, initial=False):
        icon = MediaIcon(icon_config, win_config, mounticon_config, volume,
                         screen)
        tray.add_icon(None, volume, icon)
        if not initial:
            automount_actions[mounticon_config.automount](icon)
            if mounticon_config.show_notifications:
                processes.PipeThroughCommand([
                    "notify-send",
                    "--icon=%s" % icon.find_icon_name(),
                    _("Volume \"%s\" has been inserted.") % volume.get_name()
                ], None, None).start()

    def volume_removed(volume_monitor, volume):
        icon = tray.get_icon(volume)
        try:
            del mount2icon[volume.get_mount()]
        except KeyError:
            pass
        tray.remove_icon(volume)
        if not mounticon_config.show_notifications:
            return
        if not icon.is_mounted:
            processes.PipeThroughCommand([
                "notify-send", "--icon=gtk-remove",
                _("Volume \"%s\" has been removed.") % volume.get_name()
            ], None, None).start()
        else:
            processes.PipeThroughCommand([
                "notify-send", "--icon=dialog-warning",
                _("Volume \"%s\" has been removed without unmounting. "
                "Please do always unmount a volume before removing it.") % (
                    volume.get_name()
                )
            ], None, None).start()

    def find_icon_for_mount(mount):
        mountpoint = mount.get_root()
        for icon in tray.icons:
            icon_mount = icon.get_mount()
            if icon_mount is None:
                continue
            if icon_mount.get_root() == mountpoint:
                return icon
        else:
            return None

    def mount_added(volume_monitor, mount):
        icon = find_icon_for_mount(mount)
        mount2icon[mount] = icon
        if icon is None:
            return
        if mounticon_config.show_notifications:
            processes.PipeThroughCommand([
                "notify-send",
                "--icon=%s" % icon.find_icon_name(), 
                _("Volume \"%s\" has been mounted.") % icon.name
            ], None, None).start()

    def mount_removed(volume_monitor, mount):
        try:
            icon = mount2icon.pop(mount)
        except KeyError:
            return
        if icon is None:
            return
        if mounticon_config.show_notifications:
            processes.PipeThroughCommand([
                "notify-send",
                "--icon=%s" % icon.find_icon_name(), 
                _("Volume \"%s\" has been unmounted and "
                  "can now be safely removed.") % icon.name
            ], None, None).start()

    class handlers:
        pass

    def manage():
        handlers.volume_added_handler = volume_monitor.connect("volume-added",
                                                               volume_added)
        handlers.volume_removed_handler = (
            volume_monitor.connect("volume-removed", volume_removed)
        )
        handlers.mount_added_handler = (
            volume_monitor.connect("mount-added", mount_added)
        )
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
        yield None

    return manage, unmanage
