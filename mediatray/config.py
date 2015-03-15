import os


SITE = "dtomas"
PROJECT = "MediaTray"


xdg_config_home = os.getenv("XDG_CONFIG_HOME")

if xdg_config_home is None:
    xdg_config_home = os.path.join(os.getenv("HOME"), ".config")

config_dir = os.path.join(xdg_config_home, SITE, PROJECT)
if not os.path.isdir(config_dir):
    os.makedirs(config_dir)
