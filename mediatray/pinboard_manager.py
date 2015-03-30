import os
import json

from rox import filer

from mediatray.config import config_dir


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
    if not os.path.isdir(path):
        filer.rpc.PinboardRemove(Path=path)
        filer.rpc.UnsetIcon(Path=path)

if volumes_on_pinboard:
    volumes_on_pinboard = []
    f = open(_volumes_on_pinboard_path, 'w')
    try:
        json.dump(volumes_on_pinboard, f)
    finally:
        f.close()


def add_icon_to_pinboard(icon, pinboard_config):
    """
    Add the volume to the pinboard.

    Only works if the volume is mounted and the pin option is set.
    """
    path = icon.path
    if path is None:
        return
    icon_path = icon.get_icon_path()
    if icon_path is not None:
        filer.rpc.SetIcon(Path=path, Icon=icon_path)
    filer.rpc.PinboardAdd(
        Path=path,
        Label=icon.name,
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


def remove_icon_from_pinboard(icon):
    """Remove the volume from the pinboard."""
    path = icon.path
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

    def icon_added(tray, icon):
        if not icon.is_mounted:
            return
        if not pinboard_config.pin:
            return
        add_icon_to_pinboard(icon, pinboard_config)

    def icon_mounted(tray, icon):
        if not pinboard_config.pin:
            return
        add_icon_to_pinboard(icon, pinboard_config)

    def icon_unmounted(tray, icon):
        if not pinboard_config.pin:
            return
        remove_icon_from_pinboard(icon)

    def icon_removed(tray, icon):
        if not pinboard_config.pin:
            return
        remove_icon_from_pinboard(icon)

    def pin_changed(pinboard_config):
        for icon in tray.icons:
            if not icon.is_mounted:
                continue
            if pinboard_config.pin:
                add_icon_to_pinboard(icon, pinboard_config)
            else:
                remove_icon_from_pinboard(icon)

    def pin_xy_changed(pinboard_config):
        """Called when the pin_x option has changed."""
        if not pinboard_config.pin:
            return
        for icon in tray.icons:
            if not icon.is_mounted:
                continue
            remove_icon_from_pinboard(icon)
            add_icon_to_pinboard(icon, pinboard_config)

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
        handlers.pin_changed_handler = pinboard_config.connect(
            "pin-changed", pin_changed
        )
        handlers.pin_x_changed_handler = pinboard_config.connect(
            "pin-x-changed", pin_xy_changed
        )
        handlers.pin_y_changed_handler = pinboard_config.connect(
            "pin-y-changed", pin_xy_changed
        )
        yield None

    def unmanage():
        tray.disconnect(handlers.icon_added_handler)
        tray.disconnect(handlers.icon_removed_handler)
        tray.disconnect(handlers.icon_mounted_handler)
        tray.disconnect(handlers.icon_unmounted_handler)
        pinboard_config.disconnect(handlers.pin_changed_handler)
        pinboard_config.disconnect(handlers.pin_x_changed_handler)
        pinboard_config.disconnect(handlers.pin_y_changed_handler)
        for icon in tray.icons:
            remove_icon_from_pinboard(icon)
            yield None

    return manage, unmanage