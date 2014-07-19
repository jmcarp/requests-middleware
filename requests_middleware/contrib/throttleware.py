# -*- coding: utf-8 -*-

import abc
import six
import datetime

from requests_middleware import BaseMiddleware


class ThrottleError(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class BaseThrottler(object):

    @abc.abstractmethod
    def check(self, request):
        pass

    @abc.abstractmethod
    def store(self, req, resp, response):
        pass


class DelayThrottler(BaseThrottler):

    def __init__(self, delay):
        self.delay = delay
        self.last_visit = None

    def check(self, request):
        if self.last_visit is None:
            return
        elapsed = datetime.datetime.utcnow() - self.last_visit
        if elapsed.seconds < self.delay:
            raise ThrottleError()

    def store(self, req, resp, response):
        self.last_visit = datetime.datetime.utcnow()


class RequestPerTimeThrottler(BaseThrottler):

    def __init__(self, count, resetter):
        self.count = count
        self.resetter = resetter
        self.last_reset = datetime.datetime.utcnow()
        self.visit_count = 0

    def check(self, request):
        if self.resetter(self.last_reset):
            self.last_reset = datetime.datetime.utcnow()
            self.visit_count = 0
        if self.visit_count >= self.count:
            raise ThrottleError()

    def store(self, req, resp, response):
        self.visit_count += 1


def per_hour_resetter(when):
    now = datetime.datetime.utcnow()
    return now > when and now.hour != when.hour


class RequestsPerHourThrottler(RequestPerTimeThrottler):

    def __init__(self, count):
        super(RequestsPerHourThrottler, self).__init__(count, per_hour_resetter)


class ThrottleMiddleware(BaseMiddleware):

    def __init__(self, throttler):
        self.throttler = throttler

    def before_send(self, request, *args, **kwargs):
        self.throttler.check(request)

    def after_build_response(self, req, resp, response):
        self.throttler.store(req, resp, response)
        return response
