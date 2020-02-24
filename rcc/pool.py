'''A connection pool'''

from rcc.connection import Connection


class ConnectionPool(object):
    '''Not asyncio 'thread' safe (yet)
    '''

    def __init__(self, password=None):
        self.password = password or ''
        self.connections = {}

    def get(self, url: str):
        if url not in self.connections:
            connection = Connection(url, self.password)
            self.connections[url] = connection

        return self.connections[url]
