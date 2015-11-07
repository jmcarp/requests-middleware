# -*- coding: utf-8 -*-

import pytest

import requests

from requests_middleware.middleware import MiddlewareHTTPAdapter

try:
    from requests_middleware.contrib import cachecontrolware
    has_cachecontrol = True
except ImportError:
    has_cachecontrol = False

pytestmark = pytest.mark.skipif(
    not has_cachecontrol,
    reason='cachecontrol is not installed; skipping caching tests.'
)


@pytest.fixture
def session():
    session = requests.Session()
    adapter = MiddlewareHTTPAdapter()
    cache_middleware = cachecontrolware.CacheMiddleware()
    adapter.register(cache_middleware)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Integration tests

@pytest.mark.httpretty
def test_cache_respect(session, cached_page):
    resp1 = session.get('http://test.com/cache')
    resp2 = session.get('http://test.com/cache')
    assert not getattr(resp1.raw, 'from_cache', False)
    assert getattr(resp2.raw, 'from_cache', False)


@pytest.mark.httpretty
def test_cache_respect_no_cache(session, non_cached_page):
    resp1 = session.get('http://test.com/cache')
    resp2 = session.get('http://test.com/cache')
    assert not getattr(resp1.raw, 'from_cache', False)
    assert not getattr(resp2.raw, 'from_cache', False)
