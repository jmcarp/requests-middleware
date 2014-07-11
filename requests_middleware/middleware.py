# -*- coding: utf-8 -*-

from requests.adapters import HTTPAdapter


class MiddlewareHTTPAdapter(HTTPAdapter):
    """An HTTPAdapter onto which :class:`BaseMiddleware <BaseMiddleware>`
    can be registered. Middleware methods are called in the order of
    registration. Note: contrib that expose actions called during adapter
    initialization must be passed to `__init__` rather than `register`, else
    those actions will not take effect.

    :param list middlewares: List of :class:`BaseMiddleware <BaseMiddleware>`
        objects

    """
    def __init__(self, middlewares=None, *args, **kwargs):
        self.middlewares = middlewares or []
        super(MiddlewareHTTPAdapter, self).__init__(*args, **kwargs)

    def register(self, middleware):
        """Add a middleware to the middleware stack.

        :param BaseMiddleware middleware: The middleware object

        """
        self.middlewares.append(middleware)

    def init_poolmanager(self, connections, maxsize, block=False):
        """Create the poolmanager. If any middleware in the stack returns a
        truthy value from its `before_init_poolmanager` method, short-circuit
        and return that value; else delegate to
        `HTTPAdapter::init_poolmanager`.

        """
        for middleware in self.middlewares:
            value = middleware.before_init_poolmanager(
                connections, maxsize, block
            )
            if value:
                self.poolmanager = value
                return
        super(MiddlewareHTTPAdapter, self).init_poolmanager(
            connections, maxsize, block
        )

    def send(self, request, *args, **kwargs):
        """Send the request. If any middleware in the stack returns a truthy
        value from its `before_send` method, short-circuit and return that
        value; else delegate to `HTTPAdapter::send`.

        :param request: The :class:`PreparedRequest <PreparedRequest>`
            being sent.
        :returns: The :class:`Response <Response>` object.

        """
        for middleware in self.middlewares:
            value = middleware.before_send(request, **kwargs)
            if value:
                return value
        return super(MiddlewareHTTPAdapter, self).send(
            request, *args, **kwargs
        )

    def build_response(self, req, resp):
        """Build the response. Call `HTTPAdapter::build_response`, then pass
        the response object to the `after_build_response` method of each
        middleware in the stack.

        :param req: The :class:`PreparedRequest <PreparedRequest>` used to
            generate the response.
        :param resp: The urllib3 response object.
        :returns: The :class:`Response <Response>` object.

        """
        response = super(MiddlewareHTTPAdapter, self).build_response(req, resp)
        for middleware in self.middlewares:
            response = middleware.after_build_response(req, resp, response)
        return response


class BaseMiddleware(object):

    def before_init_poolmanager(self, connections, maxsize, block=False):
        """Called before `HTTPAdapter::init_poolmanager`. If a truthy value is
        returned, :class:`MiddlewareHTTPAdapter <MiddlewareHTTPAdapter>` will
        short-circuit the remaining middlewares and `HTTPAdapter::send`, using
        the returned value instead.

        :returns: `PoolManager` or ``None``

        """
        pass

    def before_send(self, request, *args, **kwargs):
        """Triggered before calling `HTTPAdapter::send`. If a truthy value is
        returned, :class:`MiddlewareHTTPAdapter <MiddlewareHTTPAdapter>` will
        short-circuit the remaining middlewares and `HTTPAdapter::send`, using
        the returned value instead.

        :param request: The :class:`PreparedRequest <PreparedRequest>` being
            sent.
        :returns: The :class:`Response <Response>` object or ``None``.

        """
        pass

    def after_build_response(self, req, resp, response):
        """Triggered after calling `HTTPAdapter::build_response`. Optionally
        modify the returned `Response` object.

        :param req: The :class:`PreparedRequest <PreparedRequest>` used to
            generate the response.
        :param resp: The urllib3 response object.
        :param response: The :class:`Response <Response>` object.
        :returns: The potentially modified `Response` object.

        """
        return response
