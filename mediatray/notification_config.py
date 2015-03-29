from traylib.config import Config, Attribute


class NotificationConfig(Config):
    show_notifications = Attribute()
    """
    C{True} if notifications about added/removed volumes should be displayed.
    """
