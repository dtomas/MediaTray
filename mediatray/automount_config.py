from traylib.config import Config, Attribute


NO_AUTOMOUNT = 0
AUTOMOUNT = 1
AUTOOPEN = 2


class AutomountConfig(Config):
    automount = Attribute()
    """
    C{NO_AUTOMOUNT} if volumes should not be mounted automatically.
    C{AUTOMOUNT} to mount added volumes automatically.
    C{AUTOOPEN} to open added volumes automatically.
    """
