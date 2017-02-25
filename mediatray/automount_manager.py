from mediatray.automount_config import NO_AUTOMOUNT, AUTOMOUNT, AUTOOPEN
from mediatray.mountitem import MountItem


def manage_automount(tray, automount_config):

    automount_actions = {
        NO_AUTOMOUNT: lambda item: None,
        AUTOMOUNT: lambda item: item.mount(),
        AUTOOPEN: lambda item: item.open(),
    }

    def item_added(tray, box, item):
        if isinstance(item, MountItem):
            automount_actions[automount_config.automount](item)

    tray_handlers = []

    def manage():
        tray_handlers.append(tray.connect("item-added", item_added))
        yield None

    def unmanage():
        for handler in tray_handlers:
            tray.disconnect(handler)
        yield None

    return manage, unmanage
