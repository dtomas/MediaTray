import rox, os

from traylib import *
from traylib.menu_icon import MenuIcon


ICON_THEME.append_search_path(os.path.join(rox.app_dir, 'icons'))


class MainIcon(MenuIcon):

    def __init__(self, tray, icon_config, tray_config):
        MenuIcon.__init__(self, tray, icon_config, tray_config)
        tray.win_config.add_configurable(self)

    def update_option_all_workspaces(self):
        self.update_tooltip()

    def click(self, time):
        pass

    def mouse_wheel_up(self, time):
        self.tray.win_config.all_workspaces = True

    def mouse_wheel_down(self, time):
        self.tray.win_config.all_workspaces = False

    def get_icon_names(self):
        return ['computer']

    def make_tooltip(self):
        if self.tray.win_config.all_workspaces:
            s = _("Scroll down to only show windows of this workspace.")
        else:
            s = _("Scroll up to show windows of all workspaces.")
        return s
