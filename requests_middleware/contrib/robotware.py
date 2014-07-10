# -*- coding: utf-8 -*-

import datetime
import collections
from reppy.cache import RobotsCache
import six.moves.urllib_parse as urlparse
from requests_middleware import BaseMiddleware


class RobotsError(Exception):
    pass


class RobotsDisallowedError(RobotsError):
    pass


class RobotsThrottledError(RobotsError):
    pass


class RobotsMiddleware(BaseMiddleware):

    def __init__(self, *args, **kwargs):
        self.cache = RobotsCache(*args, **kwargs)
        self.visited = collections.defaultdict(dict)

    def check_disallow(self, url, agent):
        if not self.cache.allowed(url, agent):
            raise RobotsDisallowedError

    def check_crawl_delay(self, url, agent):
        delay = self.cache.delay(url, agent)
        if delay is None:
            return
        now = datetime.datetime.utcnow()
        host = urlparse.urlparse(url).hostname
        try:
            last_visit = self.visited[agent][host]
            if (now - last_visit).seconds < delay:
                raise RobotsThrottledError
        except KeyError:
            pass
        self.visited[agent][host] = now

    def before_send(self, request, *args, **kwargs):
        url = request.url
        agent = request.headers.get('User-Agent')
        self.check_disallow(url, agent)
        self.check_crawl_delay(url, agent)
