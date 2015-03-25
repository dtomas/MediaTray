import os

from mediatray.hosticon import HostIcon

from mediatray.mounticon_config import NO_AUTOMOUNT, AUTOMOUNT, AUTOOPEN


def manage_hosticons(tray, host_manager, icon_config, win_config,
                     mounticon_config, screen):

    tray.add_box("Hosts")

    automount_actions = {
        NO_AUTOMOUNT: lambda icon: None,
        AUTOMOUNT: HostIcon.mount,
        AUTOOPEN: HostIcon.open,
    }

    def host_added(host_manager, host, initial=False):
        icon = HostIcon(
            icon_config, win_config, mounticon_config, screen, host
        )
        tray.add_icon("Hosts", host, icon)
        if not initial:
            automount_actions[mounticon_config.automount](icon)

    def host_removed(host_manager, host):
        tray.remove_icon(host)

    class handlers:
        pass

    def manage():
        handlers.host_added_handler = (
            host_manager.connect("host-added", host_added)
        )
        handlers.host_removed_handler = (
            host_manager.connect("host-removed", host_removed)
        )
        for host in host_manager.hosts.itervalues():
            host_added(host_manager, host, initial=True)
            yield None

    def unmanage():
        host_manager.disconnect(handlers.host_added_handler)
        host_manager.disconnect(handlers.host_removed_handler)
        yield None

    return manage, unmanage
