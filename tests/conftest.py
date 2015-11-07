# -*- coding: utf-8 -*-

import pytest
import httpretty
import six.moves.http_client as httplib

@pytest.fixture
def page_fixture():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/page',
        body='content',
    )


@pytest.fixture
def cached_page():
    httpretty.register_uri(
        httpretty.GET,
        'http://test.com/cache',
        responses=[
            httpretty.Response(
                body='content',
                adding_headers={'ETag': 'daad3c79aab24f90a7e47742e4ed3581'},
            ),
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
