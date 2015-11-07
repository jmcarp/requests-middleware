# -*- coding: utf-8 -*-

import pytest

import datetime
import requests
from dateutil.relativedelta import relativedelta

from requests_middleware.middleware import MiddlewareHTTPAdapter
from requests_middleware.contrib import throttleware

from . import utils


@pytest.fixture
def throttle_delay():
    return throttleware.DelayThrottler(5)

@pytest.fixture
def throttle_per_hour():
    return throttleware.RequestsPerHourThrottler(5)


def make_session_fixture(throttler):
    @pytest.fixture
    def fixture():
        session = requests.Session()
        adapter = MiddlewareHTTPAdapter()
        throttle_middleware = throttleware.ThrottleMiddleware(throttler)
        adapter.register(throttle_middleware)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    return fixture


throttle_delay_session = make_session_fixture(
    throttleware.DelayThrottler(5)
)

throttle_per_hour_session = make_session_fixture(
    throttleware.RequestsPerHourThrottler(5)
)


# Unit tests

def test_throttle_delay(throttle_delay, monkeypatch):
    throttle_delay.check(None)
    throttle_delay.store(None, None, None)
    with pytest.raises(throttleware.ThrottleError):
        throttle_delay.check(None)
    now = datetime.datetime.utcnow() + relativedelta(seconds=6)
    utils.mock_datetime(monkeypatch, utcnow=now)
    throttle_delay.check(None)


def test_throttle_per_hour(throttle_per_hour, monkeypatch):
    for _ in range(5):
        throttle_per_hour.check(None)
        throttle_per_hour.store(None, None, None)
    with pytest.raises(throttleware.ThrottleError):
        throttle_per_hour.check(None)
    now = datetime.datetime.utcnow() + relativedelta(hours=2)
    utils.mock_datetime(monkeypatch, utcnow=now)
    throttle_per_hour.check(None)


# Integration tests

@pytest.mark.httpretty
def test_throttle_delay_integration(throttle_delay_session, page_fixture,
                                    monkeypatch):
    throttle_delay_session.get('http://test.com/page')
    with pytest.raises(throttleware.ThrottleError):
        throttle_delay_session.get('http://test.com/page')
    now = datetime.datetime.utcnow() + relativedelta(seconds=6)
    utils.mock_datetime(monkeypatch, utcnow=now)
    throttle_delay_session.get('http://test.com/page')


@pytest.mark.httpretty
def test_throttle_per_hour_integration(throttle_per_hour_session, page_fixture,
                                       monkeypatch):
    for _ in range(5):
        throttle_per_hour_session.get('http://test.com/page')
    with pytest.raises(throttleware.ThrottleError):
        throttle_per_hour_session.get('http://test.com/page')
    now = datetime.datetime.utcnow() + relativedelta(hours=2)
    utils.mock_datetime(monkeypatch, utcnow=now)
    throttle_per_hour_session.get('http://test.com/page')
