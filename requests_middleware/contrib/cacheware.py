# -*- coding: utf-8 -*-

import six.moves.http_client as httplib
from httpcache.cache import HTTPCache
from requests_middleware import BaseMiddleware


class CacheMiddleware(BaseMiddleware):
    
    def __init__(self, capacity=50):
        self.cache = HTTPCache(capacity=capacity)

    def before_send(self, request, *args, **kwargs):
        cached = self.cache.retrieve(request)
        if cached is not None:
            return cached

    def after_build_response(self, req, resp, response):
        if response.status_code == httplib.NOT_MODIFIED:
            response = self.cache.handle_304(response)
        else:
            self.cache.store(response)
        return response
