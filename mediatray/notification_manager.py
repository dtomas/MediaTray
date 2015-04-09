from rox import processes

from mediatray.mediaicon import MediaIcon
from mediatray.hosticon import HostIcon


def manage_notifications(tray, notification_config):

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

    def icon_mounted(tray, icon):
        if not notification_config.show_notifications:
            return
        if isinstance(icon, MediaIcon):
            msg = _("Volume \"%s\" has been mounted.")
        elif isinstance(icon, HostIcon):
            msg = _("Connected to host \"%s\".")
        else:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(), msg % icon.name
        ], None, None).start()

    def icon_unmounted(tray, icon):
        if not notification_config.show_notifications:
            return
        if isinstance(icon, MediaIcon):
            msg = _(
                "Volume \"%s\" has been unmounted and can be safely removed."
            )
        elif isinstance(icon, HostIcon):
            msg = _("Disconnected from host \"%s\".")
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(), msg % icon.name
        ], None, None).start()

    def icon_added(tray, icon):
        if not isinstance(icon, MediaIcon):
            return
        if not notification_config.show_notifications:
            return
        processes.PipeThroughCommand([
            "notify-send",
            "--icon=%s" % icon.find_icon_name(),
            _("Volume \"%s\" has been inserted.") % icon.name
        ], None, None).start()

    def icon_removed(tray, icon):
        if not isinstance(icon, MediaIcon):
            return
        if not notification_config.show_notifications:
            return
        if not icon.is_mounted:
            processes.PipeThroughCommand([
                "notify-send", "--icon=%s" % icon.find_icon_name(),
                _("Volume \"%s\" has been removed.") % icon.name
            ], None, None).start()
        else:
            processes.PipeThroughCommand([
                "notify-send", "--icon=dialog-warning",
                _("Volume \"%s\" has been removed "
                  "without unmounting.") % icon.name,
                _("Please do always unmount a volume before removing it.")
            ], None, None).start()

    class handlers:
        pass

    def manage():
        handlers.icon_added_handler = tray.connect("icon-added", icon_added)
        handlers.icon_removed_handler = tray.connect(
            "icon-removed", icon_removed
        )
        handlers.icon_mounted_handler = tray.connect(
            "icon-mounted", icon_mounted
        )
        handlers.icon_unmounted_handler = tray.connect(
            "icon-unmounted", icon_unmounted
        )
        yield None

    def unmanage():
        tray.disconnect(handlers.icon_added_handler)
        tray.disconnect(handlers.icon_removed_handler)
        tray.disconnect(handlers.icon_mounted_handler)
        tray.disconnect(handlers.icon_unmounted_handler)
        yield None

    return manage, unmanage
