# -*- coding: utf-8 -*-

import pytest
import httpretty

import ssl
import requests

from requests_middleware.middleware import MiddlewareHTTPAdapter

try:
    from requests_middleware.contrib import robotware, sslware
    has_reqs = True
except ImportError:
    has_reqs = False

pytestmark = pytest.mark.skipif(
    not has_reqs,
    reason='Requirements not installed; skipping multi-adapter tests.'
)


@pytest.fixture
def session():
    session = requests.Session()
    robots_middleware = robotware.RobotsMiddleware()
    ssl_middleware = sslware.SSLMiddleware(ssl.PROTOCOL_TLSv1)
    middlewares = [robots_middleware, ssl_middleware]
    adapter = MiddlewareHTTPAdapter(middlewares=middlewares)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


@pytest.fixture
def robots_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/robots.txt',
        body='''
            User-agent: *
            Crawl-delay: 1
        ''',
    )

@pytest.fixture
def page_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/page',
        body='content',
    )


# Integration tests

@pytest.mark.httpretty
def test_robots_and_ssl(session, robots_fixture, page_fixture):
    resp = session.get('http://test.com/page')
    pool_kwargs = resp.connection.poolmanager.connection_pool_kw
    assert pool_kwargs.get('ssl_version') == ssl.PROTOCOL_TLSv1
    with pytest.raises(robotware.RobotsThrottledError):
        session.get('http://test.com/page')
