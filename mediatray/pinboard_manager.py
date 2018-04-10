import os
import json

from rox import filer

from mediatray.config import config_dir
from mediatray.mountitem import MountItem


_volumes_on_pinboard_path = os.path.join(config_dir, 'volumes_on_pinboard')

volumes_on_pinboard = []


# remove non-existent volumes from pinboard
try:
    f = open(_volumes_on_pinboard_path, 'r')
    try:
        volumes_on_pinboard = json.load(f)
    except ValueError:
        # Unreadable file, remove it.
        os.unlink(_volumes_on_pinboard_path)
    finally:
        f.close()
except IOError:
    pass


for path in volumes_on_pinboard:
    filer.rpc.PinboardRemove(Path=path)
    filer.rpc.UnsetIcon(Path=path)

if volumes_on_pinboard:
    volumes_on_pinboard = []
    f = open(_volumes_on_pinboard_path, 'w')
    try:
        json.dump(volumes_on_pinboard, f)
    finally:
        f.close()

_paths = {}


def add_icon_to_pinboard(item, pinboard_config):
    """
    Add the volume to the pinboard.

    Only works if the volume is mounted and the pin option is set.
    """
    path = item.get_path()
    if path is None:
        return
    _paths[item] = path
    icon_path = item.find_icon_path()
    if icon_path is not None:
        filer.rpc.SetIcon(Path=path, Icon=icon_path)
    filer.rpc.PinboardAdd(
        Path=path,
        Label=item.get_name(),
        X=pinboard_config.pin_x,
        Y=pinboard_config.pin_y,
        Update=1,
    )
    if path not in volumes_on_pinboard:
        volumes_on_pinboard.append(path)
        f = open(_volumes_on_pinboard_path, 'w')
        try:
            json.dump(volumes_on_pinboard, f)
        finally:
            f.close()


def remove_icon_from_pinboard(item):
    """Remove the volume from the pinboard."""
    if item not in _paths:
        return
    path = _paths.pop(item)
    filer.rpc.PinboardRemove(Path=path)
    filer.rpc.UnsetIcon(Path=path)
    if path in volumes_on_pinboard:
        volumes_on_pinboard.remove(path)
        f = open(_volumes_on_pinboard_path, 'w')
        try:
            json.dump(volumes_on_pinboard, f)
        finally:
            f.close()


def manage_pinboard(tray, pinboard_config):

    def item_added(tray, box, item):
        if not isinstance(item, MountItem):
            return
        if not item.is_mounted:
            return
        if not pinboard_config.pin:
            return
        add_icon_to_pinboard(item, pinboard_config)

    def item_mounted(tray, item):
        if not pinboard_config.pin:
            return
        add_icon_to_pinboard(item, pinboard_config)

    def item_unmounted(tray, item):
        if not pinboard_config.pin:
            return
        remove_icon_from_pinboard(item)

    def item_removed(tray, box, item):
        if not isinstance(item, MountItem):
            return
        if not pinboard_config.pin:
            return
        remove_icon_from_pinboard(item)

    def pin_changed(pinboard_config):
        for box in tray.boxes:
            for item in box.items:
                if not isinstance(item, MountItem):
                    continue
                if not item.is_mounted:
                    continue
                if pinboard_config.pin:
                    add_icon_to_pinboard(item, pinboard_config)
                else:
                    remove_icon_from_pinboard(item)

    def pin_xy_changed(pinboard_config):
        """Called when the pin_x option has changed."""
        if not pinboard_config.pin:
            return
        for box in tray.boxes:
            for item in box.items:
                if not isinstance(item, MountItem):
                    continue
                if not item.is_mounted:
                    continue
                remove_icon_from_pinboard(item)
                add_icon_to_pinboard(item, pinboard_config)

    tray_handlers = []
    pinboard_handlers = []

    def manage():
        tray_handlers.append(tray.connect("item-added", item_added))
        tray_handlers.append(tray.connect("item-removed", item_removed))
        tray_handlers.append(tray.connect("item-mounted", item_mounted))
        tray_handlers.append(tray.connect("item-unmounted", item_unmounted))
        pinboard_handlers.append(
            pinboard_config.connect("pin-changed", pin_changed)
        )
        pinboard_handlers.append(
            pinboard_config.connect("pin-x-changed", pin_xy_changed)
        )
        pinboard_handlers.append(
            pinboard_config.connect("pin-y-changed", pin_xy_changed)
        )
        yield None

    def unmanage():
        for handler in tray_handlers:
            tray.disconnect(handler)
            tray_handlers.remove(handler)
        for handler in pinboard_handlers:
            pinboard_config.disconnect(handler)
            pinboard_handlers.remove(handler)
        for box in tray.boxes:
            for item in box.items:
                if not isinstance(item, MountItem):
                    continue
                remove_icon_from_pinboard(item)
                yield None

    return manage, unmanage
