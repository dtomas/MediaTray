import os

import gtk
import gobject


class AddHostWindow(gtk.Dialog):
    
    def __init__(self, host_manager):
        gtk.Dialog.__init__(self, _("Add Host"), 
                            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                       gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT))
        self.__host_manager = host_manager


        table = gtk.Table()

        self.vbox.pack_start(table)

        self.__protocols_model = gtk.ListStore(
            gobject.TYPE_STRING, gobject.TYPE_STRING
        )
        self.__protocols_model.append(["SSH", "ssh"])
        self.__protocols_model.append(["FTP", "ftp"])
        self.__protocols_model.append(["WebDAV", "dav"])
        self.__protocols_model.append(["SMB", "smb"])
        self.__protocol_select = gtk.ComboBox()
        self.__protocol_select.set_entry_text_column(0)
        self.__protocol_select.set_model(self.__protocols_model)
        cell = gtk.CellRendererText()
        self.__protocol_select.pack_start(cell, True)
        self.__protocol_select.add_attribute(cell, 'text', 0)

        self.__hostname_input = gtk.Entry()
        self.__username_input = gtk.Entry()
        self.__path_input = gtk.Entry()
        self.__port_select = gtk.SpinButton(gtk.Adjustment(0, 0, 65534, 1), 1)

        table.attach(gtk.Label(_("Protocol")), 0, 1, 0, 1)
        table.attach(gtk.Label(_("Hostname")), 0, 1, 1, 2)
        table.attach(gtk.Label(_("Username")), 0, 1, 2, 3)
        table.attach(gtk.Label(_("Port")), 0, 1, 3, 4)
        table.attach(gtk.Label(_("Path")), 0, 1, 4, 5)

        table.attach(self.__protocol_select, 1, 2, 0, 1)
        table.attach(self.__hostname_input, 1, 2, 1, 2)
        table.attach(self.__username_input, 1, 2, 2, 3)
        table.attach(self.__port_select, 1, 2, 3, 4)
        table.attach(self.__path_input, 1, 2, 4, 5)

        def response(dialog, response_id):
            if response_id == gtk.RESPONSE_ACCEPT:
                column = self.__protocol_select.get_property("active")
                iter = self.__protocols_model.get_iter((column,))
                protocol = self.__protocols_model.get(iter, 1)[0]
                port = self.__port_select.get_value()
                uri = '{protocol}://{username}@{hostname}{port}/{path}'.format(
                    protocol=protocol,
                    username=self.__username_input.get_text(),
                    hostname=self.__hostname_input.get_text(),
                    path=self.__path_input.get_text(),
                    port=':%s' % port if port != 0 else '',
                )
                self.__host_manager.add_host(uri)
            dialog.destroy()
        self.connect("response", response)
        self.show_all()
