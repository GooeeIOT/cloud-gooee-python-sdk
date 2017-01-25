# -*- coding: utf-8 -*-

from requests.exceptions import ConnectionError


class GooeeException(Exception):
    pass


class IllegalHttpMethod(GooeeException):
    pass


class InvalidResourcePath(GooeeException):
    pass


class UnknownEndpoint(GooeeException):
    pass


class UnsupportedEndpoint(GooeeException):
    pass


class InternetConnectionError(ConnectionError):
    """
    Wraps requests.exceptions.ConnectionError in order to provide a more
    intuitively named exception.
    """
    pass
