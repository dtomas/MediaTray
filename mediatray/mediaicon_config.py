from traylib.config import Config


PIN_LEFT = -1
PIN_TOP = -1
PIN_RIGHT = -2
PIN_BOTTOM = -2


class MediaIconConfig(Config):
    
    def __init__(self, pin, pin_x, pin_y):
        Config.__init__(self)
        self.add_attribute('pin', pin, 'update_pin')
        self.add_attribute('pin_x', pin_x, 'update_pin_x')
        self.add_attribute('pin_y', pin_y, 'update_pin_y')

    pin = property(
        lambda self : self.get_attribute('pin'),
        lambda self, pin : self.set_attribute('pin', pin)
    )
    pin_x = property(
        lambda self : self.get_attribute('pin_x'),
        lambda self, pin_x : self.set_attribute('pin_x', pin_x)
    )
    pin_y = property(
        lambda self : self.get_attribute('pin_y'),
        lambda self, pin_y : self.set_attribute('pin_y', pin_y)
    )
