# -*- coding: utf-8 -*-

import pytest

import requests

from requests_middleware.middleware import MiddlewareHTTPAdapter

try:
    from requests_middleware.contrib import httpcacheware
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
    cache_middleware = httpcacheware.CacheMiddleware()
    adapter.register(cache_middleware)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


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
