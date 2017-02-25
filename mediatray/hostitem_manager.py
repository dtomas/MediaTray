from traylib.item_box import ItemBox

from mediatray.hostitem import HostItem


def manage_hostitems(tray, host_manager, win_config, screen, volume_monitor):

    class state:
        box = None
        handlers = []

    def host_added(host_manager, host):
        print("adding host %s" % host.name)
        state.box.add_item(
            HostItem(win_config, screen, host_manager, host, volume_monitor)
        )

    def host_removed(host_manager, host):
        for item in state.box.items:
            if item.host is host:
                state.box.remove_item(item)
                break

    def manage():
        state.box = ItemBox("hosts")
        tray.add_box(state.box)
        state.handlers = [
            host_manager.connect("host-added", host_added),
            host_manager.connect("host-removed", host_removed),
        ]
        for host in host_manager.hosts.itervalues():
            host_added(host_manager, host)
            yield None

    def unmanage():
        for handler in state.handlers:
            host_manager.disconnect(handler)
        state.handlers = []
        tray.remove_box(state.box)
        state.box = None
        yield None

    return manage, unmanage
