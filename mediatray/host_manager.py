import os
import json
import urlparse

import gobject

from mediatray.config import config_dir


_hosts_path = os.path.join(config_dir, 'hosts')

_hosts = []

try:
    f = open(_hosts_path, 'r')
    try:
        _hosts = json.load(f)
    except ValueError:
        # Unreadable file, remove it.
        os.unlink(_hosts_path)
    finally:
        f.close()
except IOError:
    pass


def _save_hosts():
    f = open(_hosts_path, 'w')
    try:
        json.dump(_hosts, f)
    finally:
        f.close()


class HostManager(gobject.GObject):
    
    def __init__(self):
        gobject.GObject.__init__(self)

        host_manager = self

        class Host(object):

            def __init__(self, uri):
                parsed_uri = urlparse.urlparse(uri)
                self.__uri = uri
                self.__name = parsed_uri.netloc
                self.__uri_scheme = parsed_uri.scheme

            def remove(self):
                host_manager.remove_host(self.__uri)

            uri = property(lambda self : self.__uri)
            name = property(lambda self : self.__name)
            uri_scheme = property(lambda self : self.__uri_scheme)

        self.__Host = Host

        self.__hosts = {uri: Host(uri) for uri in _hosts}

    def add_host(self, uri):
        self.__hosts[uri] = host = self.__Host(uri)
        _hosts.append(uri)
        _save_hosts()
        self.emit("host-added", host)

    def remove_host(self, uri):
        _hosts.remove(uri)
        _save_hosts()
        self.emit("host-removed", self.__hosts.pop(uri))

    hosts = property(lambda self : self.__hosts)


gobject.type_register(HostManager)
gobject.signal_new(
    "host-added", HostManager, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
    (object,)
)
gobject.signal_new(
    "host-removed", HostManager, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
    (object,)
)
