# -*- coding: utf-8 -*-

import pytest
import httpretty

import time
import datetime
import requests
import six.moves.http_client as httplib
from dateutil.relativedelta import relativedelta

from requests_middleware.middleware import MiddlewareHTTPAdapter

from . import utils

try:
    from requests_middleware.contrib import robotware
    from reppy.parser import Rules
    has_reppy = True
except ImportError:
    has_reppy = False

pytestmark = pytest.mark.skipif(
    not has_reppy,
    reason='reppy is not installed; skipping robots tests.'
)


@pytest.fixture
def session():
    session = requests.Session()
    session.headers['User-Agent'] = 'robot'
    adapter = MiddlewareHTTPAdapter()
    robots_middleware = robotware.RobotsMiddleware()
    adapter.register(robots_middleware)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def make_middleware_fixture(rules):
    @pytest.fixture
    def fixture():
        middleware = robotware.RobotsMiddleware()
        middleware.cache.add(
            Rules(
                'http://test.com/robots.txt',
                httplib.OK,
                rules,
                time.time() * 2,
            )
        )
        return middleware
    return fixture

delay_middleware = make_middleware_fixture('''
    User-agent: robot
    Disallow: /blocked
    Crawl-Delay: 1
''')

no_delay_middleware = make_middleware_fixture('''
    User-agent: robot
    Disallow: /blocked
''')


@pytest.fixture
def robots_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/robots.txt',
        body='''
            User-agent: robot
            Disallow: /blocked
            Crawl-Delay: 1
        ''',
    )

@pytest.fixture
def plain_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/plain',
        body=u'no robots behaviör',
    )

@pytest.fixture
def blocked_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/blocked',
        body='cant touch this',
    )


# Unit tests

def test_check_crawl_delay_none(no_delay_middleware):
    no_delay_middleware.check_crawl_delay('http://test.com/plain', 'robot')
    assert no_delay_middleware.visited == {}


def test_check_crawl_delay_ok(delay_middleware, monkeypatch):
    now = datetime.datetime.utcnow()
    utils.mock_datetime(monkeypatch, utcnow=now)
    delay_middleware.check_crawl_delay('http://test.com/plain', 'robot')
    assert delay_middleware.visited['robot']['test.com'] == now
    assert delay_middleware.visited['human'] == {}


def test_check_crawl_delay_throttled(delay_middleware):
    delay_middleware.check_crawl_delay('http://test.com/plain', 'robot')
    delay_middleware.check_crawl_delay('http://test.com/plain', 'human')
    with pytest.raises(robotware.RobotsThrottledError):
        delay_middleware.check_crawl_delay('http://test.com/plain', 'robot')


# Integration tests

@pytest.mark.httpretty
def test_plain(session, robots_fixture, plain_fixture):
    session.get('http://test.com/plain')


@pytest.mark.httpretty
def test_disallow_disallowed_agent(session, robots_fixture, blocked_fixture):
    with pytest.raises(robotware.RobotsDisallowedError):
        session.get('http://test.com/blocked')


@pytest.mark.httpretty
def test_disallow_allowed_agent(session, robots_fixture, blocked_fixture):
    session.get('http://test.com/blocked', headers={'User-Agent': 'human'})


@pytest.mark.httpretty
def test_delay(session, robots_fixture, plain_fixture, monkeypatch):
    session.get('http://test.com/plain')
    session.get('http://test.com/plain', headers={'User-Agent': 'human'})
    with pytest.raises(robotware.RobotsThrottledError):
        session.get('http://test.com/plain')
    now = datetime.datetime.utcnow() + relativedelta(seconds=5)
    utils.mock_datetime(monkeypatch, utcnow=now)
    session.get('http://test.com/plain')
