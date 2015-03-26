import gio


def manage_mounticons(tray, mounticon_config):

    volume_monitor = gio.volume_monitor_get()

    def mount_added(volume_monitor, mount):
        mountpoint = mount.get_root()
        for icon in tray.icons:
            if icon.get_mount() is None:
                continue
            if icon.get_mount().get_root() == mountpoint:
                icon.mounted()

    class handlers:
        pass

    def manage():
        handlers.mount_added_handler = volume_monitor.connect("mount-added",
                                                              mount_added)
        yield None

    def unmanage():
        volume_monitor.disconnect(handlers.mount_added_handler)
        for icon in tray.icons:
            if not icon.is_mounted:
                continue
            icon.remove_from_pinboard(icon.mountpoint)
        yield None

    return manage, unmanage
