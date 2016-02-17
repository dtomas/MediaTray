from rox import processes

from mediatray.mediaicon import MediaIcon


def manage_notifications(tray, notification_config):

    def icon_mounted(tray, icon):
        if not notification_config.show_notifications:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(),
            icon.get_mounted_message()
        ], None, None).start()

    def icon_unmounted(tray, icon):
        if not notification_config.show_notifications:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(),
            icon.get_unmounted_message()
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

    tray_handlers = []

    def manage():
        tray_handlers.append(tray.connect("icon-added", icon_added))
        tray_handlers.append(tray.connect("icon-removed", icon_removed))
        tray_handlers.append(tray.connect("icon-mounted", icon_mounted))
        tray_handlers.append(tray.connect("icon-unmounted", icon_unmounted))
        yield None

    def unmanage():
        for handler in tray_handlers:
            tray.disconnect(handler)
        yield None

    return manage, unmanage
