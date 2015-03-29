import os

from mediatray.hosticon import HostIcon


def manage_hosticons(tray, host_manager, icon_config, win_config, screen,
                     volume_monitor):

    tray.add_box("Hosts")

    def host_added(host_manager, host):
        tray.add_icon("Hosts", host, HostIcon(
            icon_config, win_config, screen, host_manager, host, volume_monitor
        ))

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
            host_added(host_manager, host)
            yield None

    def unmanage():
        host_manager.disconnect(handlers.host_added_handler)
        host_manager.disconnect(handlers.host_removed_handler)
        yield None

    return manage, unmanage
