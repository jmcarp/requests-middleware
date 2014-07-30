# -*- coding: utf-8 -*-

import pytest
import pytest_httpretty

import ssl
import requests

from requests_middleware.middleware import MiddlewareHTTPAdapter
from requests_middleware.contrib import sslware

from .fixtures import page_fixture


@pytest.fixture
def session():
    session = requests.Session()
    ssl_middleware = sslware.SSLMiddleware(ssl.PROTOCOL_TLSv1)
    middlewares = [ssl_middleware]
    adapter = MiddlewareHTTPAdapter(middlewares=middlewares)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Integration tests

@pytest.mark.httpretty
def test_ssl(session, page_fixture):
    resp = session.get('http://test.com/page')
    pool_kwargs = resp.connection.poolmanager.connection_pool_kw
    assert pool_kwargs.get('ssl_version') == ssl.PROTOCOL_TLSv1
