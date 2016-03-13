import os

from traylib.winitem import create_window_item

from mediatray.mountitem import MountItem


def manage_winitems(tray, win_config, screen):

    class state:
        screen_handlers = []
        window_item_handlers = {}

    def update_window_item(window_item):
        path = os.path.realpath(window_item.get_path())
        for box in tray.boxes:
            for item in box.items:
                if not isinstance(item, MountItem):
                    continue
                if item.get_path() is None:
                    continue
                if window_item in item.window_items:
                    if not path.startswith(os.path.realpath(item.get_path())):
                        item.remove_window_item(window_item)
                else:
                    if path.startswith(os.path.realpath(item.get_path())):
                        item.add_window_item(window_item)
    
    def window_item_destroyed(window_item):
        for handler in state.window_item_handlers.pop(window_item):
            window_item.disconnect(handler)

    def window_item_changed(window_item, props):
        if "path" in props:
            update_window_item(window_item)

    def window_opened(screen, window):
        window_item = create_window_item(window, win_config)
        if not hasattr(window_item, "get_path"):
            return
        state.window_item_handlers[window_item] = [
            window_item.connect("changed", window_item_changed),
            window_item.connect("destroyed", window_item_destroyed),
        ]
        update_window_item(window_item)

    def manage():
        state.screen_handlers = [
            screen.connect("window-opened", window_opened),
        ]
        for window in screen.get_windows():
            window_opened(screen, window)
            yield None

    def unmanage():
        for handler in state.screen_handlers:
            screen.disconnect(handler)
        state.screen_handlers = []
        yield None

    return manage, unmanage
