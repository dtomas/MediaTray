from traylib.config import Config, Attribute


PIN_LEFT = -1
PIN_TOP = -1
PIN_RIGHT = -2
PIN_BOTTOM = -2

AUTOMOUNT = 1
AUTOOPEN = 2


class MediaIconConfig(Config):
    pin = Attribute()
    pin_x = Attribute()
    pin_y = Attribute()
    automount = Attribute()
