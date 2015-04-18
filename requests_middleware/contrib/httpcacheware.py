# -*- coding: utf-8 -*-

from httpcache.cache import HTTPCache
import six.moves.http_client as httplib

from requests_middleware import BaseMiddleware


class CacheMiddleware(BaseMiddleware):

    def __init__(self, capacity=50):
        self.cache = HTTPCache(capacity=capacity)

    def before_send(self, request, *args, **kwargs):
        """Adapted from `CachingHTTPAdapter::send`. Check for cached response
        and update request with conditional headers.
        """
        cached = self.cache.retrieve(request)
        if cached is not None:
            return cached

    def after_build_response(self, req, resp, response):
        """Adapted from `CachingHTTPAdapter::build_response`. Fetch cached
        response if appropriate and mark with `from_cache`.

        """
        if response.status_code == httplib.NOT_MODIFIED:
            response = self.cache.handle_304(response)
        else:
            self.cache.store(response)
        return response
