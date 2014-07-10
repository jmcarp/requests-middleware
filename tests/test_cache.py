# -*- coding: utf-8 -*-

import pytest
import httpretty
import pytest_httpretty

import requests
import six.moves.http_client as httplib

from requests_middleware.middleware import MiddlewareHTTPAdapter

try:
    from requests_middleware.contrib import cacheware
    has_httpcache = True
except ImportError:
    has_httpcache = False

pytestmark = pytest.mark.skipif(
    not has_httpcache,
    reason='httpcache is not installed; skipping caching tests.'
)


@pytest.fixture
def session():
    session = requests.Session()
    adapter = MiddlewareHTTPAdapter()
    cache_middleware = cacheware.CacheMiddleware()
    adapter.register(cache_middleware)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


@pytest.fixture
def cached_page():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/cache',
        responses=[
            httpretty.Response(body='content'),
            httpretty.Response(body='', status=httplib.NOT_MODIFIED),
        ]
    )

@pytest.fixture
def non_cached_page():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/cache',
        body='content',
    )


# Integration tests

@pytest.mark.httpretty
def test_cache_respect(session, cached_page):
    resp1 = session.get('http://test.com/cache')
    resp2 = session.get('http://test.com/cache')
    assert resp1 is resp2

@pytest.mark.httpretty
def test_cache_respect_no_cache(session, non_cached_page):
    resp1 = session.get('http://test.com/cache')
    resp2 = session.get('http://test.com/cache')
    assert resp1 is not resp2
