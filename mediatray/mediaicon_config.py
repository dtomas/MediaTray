from traylib.config import Config, Attribute


PIN_LEFT = -1
PIN_TOP = -1
PIN_RIGHT = -2
PIN_BOTTOM = -2

NO_AUTOMOUNT = 0
AUTOMOUNT = 1
AUTOOPEN = 2


class MediaIconConfig(Config):
    pin = Attribute()
    """C{True} if icons should be added to the pinboard."""

    pin_x = Attribute()
    """
    C{PIN_LEFT} to add icons on the left or C{PIN_RIGHT} to add icons on the
    right.
    """

    pin_y = Attribute()
    """
    C{PIN_TOP} to add icons on the top or C{PIN_BOTTOM} to add icons on the
    bottom.
    """

    automount = Attribute()
    """
    C{NO_AUTOMOUNT} if volumes should not be mounted automatically.
    C{AUTOMOUNT} to mount added volumes automatically.
    C{AUTOOPEN} to open added volumes automatically.
    """
