# -*- coding: utf-8 -*-

import six
import mock
import datetime


def mock_datetime(monkeypatch, **kwargs):
    fake = mock.Mock(auto_spec=datetime.datetime)
    for key, value in six.iteritems(kwargs):
        method = getattr(fake, key)
        method.return_value = value
    monkeypatch.setattr(datetime, 'datetime', fake)
