from mediatray.automount_config import NO_AUTOMOUNT, AUTOMOUNT, AUTOOPEN


def manage_automount(tray, automount_config):

    automount_actions = {
        NO_AUTOMOUNT: lambda icon: None,
        AUTOMOUNT: lambda icon: icon.mount(),
        AUTOOPEN: lambda icon: icon.open(),
    }

    def icon_added(tray, icon):
        automount_actions[automount_config.automount](icon)

    class handlers:
        pass

    def manage():
        handlers.icon_added_handler = tray.connect("icon-added", icon_added)
        yield None

    def unmanage():
        tray.disconnect(handlers.icon_added_handler)
        yield None

    return manage, unmanage
