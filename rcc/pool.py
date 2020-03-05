'''A connection pool'''

from rcc.connection import Connection


class ConnectionPool(object):
    '''Not asyncio 'thread' safe (yet)
    '''

    def __init__(self, password=None, multiplexing=False):
        self.password = password or ''
        self.connections = {}
        self.multiplexing = multiplexing

    def __del__(self):
        self.flush()

    def get(self, url: str):
        if url not in self.connections:
            connection = Connection(url, self.password, self.multiplexing)
            self.connections[url] = connection

        return self.connections[url]

    def flush(self):
        for connection in self.connections.values():
            connection.close()
