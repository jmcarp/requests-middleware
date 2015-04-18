# -*- coding: utf-8 -*-

from requests_middleware import BaseMiddleware


class SourceMiddleware(BaseMiddleware):

    def __init__(self, address, port):
        self.address = address
        self.port = port

    def before_init_poolmanager(self, connections, maxsize, block=False):
        return {'source_address': (self.address, self.port)}
