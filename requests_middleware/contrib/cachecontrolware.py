# -*- coding: utf-8 -*-

import functools

from cachecontrol.cache import DictCache
from cachecontrol.controller import CacheController
from cachecontrol.filewrapper import CallbackFileWrapper

from requests_middleware import BaseMiddleware


INVALIDATING_METHODS = set(['PUT', 'DELETE'])


class CacheMiddleware(BaseMiddleware):

    def __init__(self, cache=None, cache_etags=True, controller_class=None,
                 serializer=None, heuristic=None):
        self.cache = cache or DictCache()
        self.heuristic = heuristic
        controller_factory = controller_class or CacheController
        self.controller = controller_factory(
            self.cache,
            cache_etags=cache_etags,
            serializer=serializer,
        )

    def before_send(self, request, *args, **kwargs):
        """Adapted from `CacheControlAdapter::send`. Check for cached response
        and update request with conditional headers.
        """
        if request.method == 'GET':
            cached_resp = self.controller.cached_request(request)
            if cached_resp:
                return cached_resp
            request.headers.update(self.controller.conditional_headers(request))

    def before_build_response(self, request, response):
        """Adapted from `CacheControlAdapter::build_response`. Fetch cached
        response if appropriate and mark with `from_cache`.
        """
        from_cache = getattr(response, 'from_cache', False)

        if request.method == 'GET' and not from_cache:
            if response.status == 304:
                cached_response = self.controller.update_cached_response(
                    request, response
                )
                if cached_response is not response:
                    from_cache = True
                response = cached_response
            else:
                if self.heuristic:
                    response = self.heuristic.apply(response)
                response._fp = CallbackFileWrapper(
                    response._fp,
                    functools.partial(
                        self.controller.cache_response,
                        request,
                        response,
                    )
                )

        if request.method in INVALIDATING_METHODS and response.ok:
            cache_url = self.controller.cache_url(request.url)
            self.cache.delete(cache_url)

        response.from_cache = from_cache

        return request, response
