from gi.repository import Gtk
from gi.repository import GObject


class HostEditor(Gtk.Dialog):

    def __init__(self, host_manager, host=None):
        GObject.GObject.__init__(
            self, _("Add Host") if host is None else _("Edit Host"),
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                Gtk.STOCK_SAVE if host is not None
                else Gtk.STOCK_ADD, Gtk.ResponseType.ACCEPT
            ),
        )
        self.__host_manager = host_manager
        self.__host = host

        table = Gtk.Table()

        self.vbox.pack_start(table, True, True, 0)

        self.__protocols_model = Gtk.ListStore(
            GObject.TYPE_STRING, GObject.TYPE_STRING
        )
        self.__protocols_model.append(["SSH", "ssh"])
        self.__protocols_model.append(["FTP", "ftp"])
        self.__protocols_model.append(["WebDAV", "dav"])
        self.__protocols_model.append(["SMB", "smb"])
        self.__protocol_select = Gtk.ComboBox()
        self.__protocol_select.set_entry_text_column(0)
        self.__protocol_select.set_model(self.__protocols_model)
        cell = Gtk.CellRendererText()
        self.__protocol_select.pack_start(cell, True)
        self.__protocol_select.add_attribute(cell, 'text', 0)

        self.__hostname_input = Gtk.Entry()
        self.__username_input = Gtk.Entry()
        self.__path_input = Gtk.Entry()
        self.__port_select = Gtk.SpinButton(Gtk.Adjustment(0, 0, 65534, 1), 1)

        self.__hostname_error = Gtk.Label()
        self.__port_error = Gtk.Label()
        self.__protocol_error = Gtk.Label()

        if self.__host is not None:
            self.__hostname_input.set_text(self.__host.hostname)
            self.__username_input.set_text(self.__host.username)
            self.__path_input.set_text(self.__host.path)
            self.__port_select.set_value(self.__host.port)
            iter = self.__protocols_model.get_iter_first()
            while iter:
                protocol = self.__protocols_model.get_value(iter, 1)
                if protocol == self.__host.protocol:
                    self.__protocol_select.set_active_iter(iter)
                    break
                iter = self.__protocols_model.iter_next(iter)

        table.attach(self.__protocol_error, 0, 2, 0, 1)
        table.attach(Gtk.Label(label=_("Protocol")), 0, 1, 1, 2)
        table.attach(self.__hostname_error, 0, 2, 2, 3)
        table.attach(Gtk.Label(label=_("Hostname")), 0, 1, 3, 4)
        table.attach(Gtk.Label(label=_("Username")), 0, 1, 4, 5)
        table.attach(Gtk.Label(label=_("Port")), 0, 1, 5, 6)
        table.attach(Gtk.Label(label=_("Path")), 0, 1, 6, 7)

        table.attach(self.__protocol_select, 1, 2, 1, 2)
        table.attach(self.__hostname_input, 1, 2, 3, 4)
        table.attach(self.__username_input, 1, 2, 4, 5)
        table.attach(self.__port_select, 1, 2, 5, 6)
        table.attach(self.__path_input, 1, 2, 6, 7)

        def clear_errors():
            self.__protocol_error.hide()
            self.__hostname_error.hide()

        def response(dialog, response_id):
            clear_errors()
            if response_id == Gtk.ResponseType.ACCEPT:
                has_error = False
                hostname = self.__hostname_input.get_text()
                if not hostname:
                    has_error = True
                    self.__hostname_error.set_text(
                        _("You must enter a hostname.")
                    )
                    self.__hostname_error.show()
                column = self.__protocol_select.get_property("active")
                try:
                    iter = self.__protocols_model.get_iter((column,))
                except ValueError:
                    has_error = True
                    self.__protocol_error.set_text(
                        _("You must select a protocol.")
                    )
                    self.__protocol_error.show()
                else:
                    protocol = self.__protocols_model.get(iter, 1)[0]
                if has_error:
                    return
                port = self.__port_select.get_value()
                username = self.__username_input.get_text()
                uri = '{protocol}://{username}{hostname}{port}/{path}'.format(
                    protocol=protocol,
                    username='%s@' % username if username else '',
                    hostname=self.__hostname_input.get_text(),
                    path=self.__path_input.get_text().lstrip('/'),
                    port=':%s' % port if port != 0 else '',
                )
                if self.__host is not None:
                    self.__host_manager.update_host(self.__host.uri, uri)
                else:
                    self.__host_manager.add_host(uri)
            dialog.destroy()
        self.connect("response", response)
        self.show_all()
        clear_errors()
