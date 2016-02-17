from rox import processes


def manage_notifications(tray, notification_config):

    def icon_mounted(tray, icon):
        if not notification_config.show_notifications:
            return
        msg = icon.get_mounted_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(), msg
        ], None, None).start()

    def icon_unmounted(tray, icon):
        if not notification_config.show_notifications:
            return
        msg = icon.get_unmounted_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(), msg
        ], None, None).start()

    def icon_added(tray, icon):
        if not notification_config.show_notifications:
            return
        msg = icon.get_added_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send",
            "--icon=%s" % icon.find_icon_name(), msg
        ], None, None).start()

    def icon_removed(tray, icon):
        if not notification_config.show_notifications:
            return
        msg = icon.get_removed_message()
        if not msg:
            return
        detail = icon.get_removed_detail()
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % icon.find_icon_name(), msg, detail
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
