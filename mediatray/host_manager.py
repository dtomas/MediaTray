import os
import json
import urlparse

from gi.repository import GObject

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


class HostManager(GObject.GObject):
    
    def __init__(self):
        GObject.GObject.__init__(self)

        host_manager = self

        class Host(GObject.GObject):

            def __init__(self, uri):
                GObject.GObject.__init__(self)
                self.uri = uri

            @property
            def uri(self):
                return self.__uri

            @uri.setter
            def uri(self, uri):
                changed = hasattr(self, '_Host__uri')
                self.__uri = uri
                parsed_uri = urlparse.urlparse(uri)
                self.__name = parsed_uri.netloc
                self.__protocol = parsed_uri.scheme
                tmp = parsed_uri.netloc.split(':')
                self.__port = tmp[1] if len(tmp) == 2 else 0
                name = tmp[0]
                tmp = name.split('@')
                if len(tmp) == 2:
                    self.__username = tmp[0]
                    self.__hostname = tmp[1]
                else:
                    self.__username = ''
                    self.__hostname = tmp[0]
                self.__path = parsed_uri.path
                self.__title = parsed_uri.netloc
                if changed:
                    self.emit("changed")

            def remove(self):
                host_manager.remove_host(self.__uri)

            protocol = property(lambda self : self.__protocol)
            name = property(lambda self : self.__name)
            hostname = property(lambda self : self.__hostname)
            username = property(lambda self : self.__username)
            port = property(lambda self : self.__port)
            path = property(lambda self : self.__path)
            title = property(lambda self : self.__title)

        GObject.type_register(Host)
        GObject.signal_new(
            "changed", Host, GObject.SignalFlags.RUN_FIRST, None, ()
        )

        self.__Host = Host

        self.__hosts = {uri: Host(uri) for uri in _hosts}

    def add_host(self, uri):
        self.__hosts[uri] = host = self.__Host(uri)
        _hosts.append(uri)
        _save_hosts()
        self.emit("host-added", host)

    def update_host(self, old_uri, new_uri):
        host = self.__hosts.pop(old_uri)
        host.uri = new_uri
        self.__hosts[new_uri] = host
        i = _hosts.index(old_uri)
        _hosts.remove(old_uri)
        _hosts.insert(i, new_uri)
        _save_hosts()

    def remove_host(self, uri):
        _hosts.remove(uri)
        _save_hosts()
        self.emit("host-removed", self.__hosts.pop(uri))

    hosts = property(lambda self : self.__hosts)


GObject.type_register(HostManager)
GObject.signal_new(
    "host-added", HostManager, GObject.SignalFlags.RUN_FIRST, None,
    (GObject.GObject,)
)
GObject.signal_new(
    "host-removed", HostManager, GObject.SignalFlags.RUN_FIRST, None,
    (GObject.GObject,)
)
