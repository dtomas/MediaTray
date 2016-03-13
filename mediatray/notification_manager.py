from rox import processes

from mediatray.mountitem import MountItem


def manage_notifications(tray, notification_config):

    def item_mounted(tray, item):
        if not notification_config.show_notifications:
            return
        msg = item.get_mounted_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % item.find_icon_name(), msg
        ], None, None).start()

    def item_unmounted(tray, item):
        if not notification_config.show_notifications:
            return
        msg = item.get_unmounted_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % item.find_icon_name(), msg
        ], None, None).start()

    def item_added(tray, box, item):
        if not isinstance(item, MountItem):
            return
        if not notification_config.show_notifications:
            return
        msg = item.get_added_message()
        if not msg:
            return
        processes.PipeThroughCommand([
            "notify-send",
            "--icon=%s" % item.find_icon_name(), msg
        ], None, None).start()

    def item_removed(tray, box, item):
        if not isinstance(item, MountItem):
            return
        if not notification_config.show_notifications:
            return
        msg = item.get_removed_message()
        if not msg:
            return
        detail = item.get_removed_detail()
        processes.PipeThroughCommand([
            "notify-send", "--icon=%s" % item.find_icon_name(), msg, detail
        ], None, None).start()

    tray_handlers = []

    def manage():
        tray_handlers.append(tray.connect("item-added", item_added))
        tray_handlers.append(tray.connect("item-removed", item_removed))
        tray_handlers.append(tray.connect("item-mounted", item_mounted))
        tray_handlers.append(tray.connect("item-unmounted", item_unmounted))
        yield None

    def unmanage():
        for handler in tray_handlers:
            tray.disconnect(handler)
            tray_handlers.remove(handler)
            yield None

    return manage, unmanage
