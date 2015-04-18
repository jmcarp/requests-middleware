# -*- coding: utf-8 -*-

from requests_middleware import BaseMiddleware


class SSLMiddleware(BaseMiddleware):

    def __init__(self, ssl_version):
        self.ssl_version = ssl_version

    def before_init_poolmanager(self, connections, maxsize, block=False):
        return {'ssl_version': self.ssl_version}
