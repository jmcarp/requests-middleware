# -*- coding: utf-8 -*-

import functools
import six.moves.http_client as httplib

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

    def before_build_response(self, req, resp):
        """Adapted from `CacheControlAdapter::build_response`. Fetch cached
        response if appropriate and mark with `from_cache`.

        """
        from_cache = getattr(resp, 'from_cache', False)

        if req.method == 'GET' and not from_cache:
            if resp.status == 304:
                cached_resp = self.controller.update_cached_response(
                    req, resp
                )
                if cached_resp is not resp:
                    from_cache = True
                resp = cached_resp
            else:
                if self.heuristic:
                    resp = self.heuristic.apply(resp)
                resp._fp = CallbackFileWrapper(
                    resp._fp,
                    functools.partial(
                        self.controller.cache_response,
                        req,
                        resp,
                    )
                )

        if req.method in INVALIDATING_METHODS and resp.ok:
            cache_url = self.controller.cache_url(request.url)
            self.cache.delete(cache_url)

        resp.from_cache = from_cache

        return req, resp

