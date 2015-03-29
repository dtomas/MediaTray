from traylib.config import Config, Attribute


PIN_LEFT = -1
PIN_TOP = -1
PIN_RIGHT = -2
PIN_BOTTOM = -2


class PinboardConfig(Config):
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
