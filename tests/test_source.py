# -*- coding: utf-8 -*-

import pytest

import requests

from requests_middleware.middleware import MiddlewareHTTPAdapter
from requests_middleware.contrib import sourceware


@pytest.fixture
def session():
    session = requests.Session()
    source_middleware = sourceware.SourceMiddleware('localhost', 8080)
    middlewares = [source_middleware]
    adapter = MiddlewareHTTPAdapter(middlewares=middlewares)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Integration tests

@pytest.mark.httpretty
def test_source(session, page_fixture):
    resp = session.get('http://test.com/page')
    pool_kwargs = resp.connection.poolmanager.connection_pool_kw
    assert pool_kwargs.get('source_address') == ('localhost', 8080)
