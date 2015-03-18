import os

from rox.basedir import xdg_config_home


SITE = "dtomas"
PROJECT = "MediaTray"


config_dir = os.path.join(xdg_config_home, SITE, PROJECT)
if not os.path.isdir(config_dir):
    os.makedirs(config_dir)
