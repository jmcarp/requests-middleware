# -*- coding: utf-8 -*-

from requests.packages.urllib3.poolmanager import PoolManager
from requests_middleware import BaseMiddleware


class SSLMiddleware(BaseMiddleware):
    
    def __init__(self, ssl_version):
        self.ssl_version = ssl_version

    def before_init_poolmanager(self, connections, maxsize, block=False,
                                **pool_kwargs):
        return PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=self.ssl_version,
            **pool_kwargs
        )
