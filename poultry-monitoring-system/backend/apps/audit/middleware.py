"""Thread-local current-user tracking used by audit columns and AuditLog."""
from contextlib import contextmanager
from threading import local

_state = local()


def get_current_user():
    return getattr(_state, "user", None)


def get_current_request():
    return getattr(_state, "request", None)


@contextmanager
def set_current_user(user):
    """Context manager to set the acting user (used by management commands)."""
    previous = getattr(_state, "user", None)
    _state.user = user
    try:
        yield
    finally:
        _state.user = previous


class CurrentUserMiddleware:
    """Store the request user in thread-local storage for the request cycle."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.user = getattr(request, "user", None)
        _state.request = request
        try:
            response = self.get_response(request)
        finally:
            _state.user = None
            _state.request = None
        return response
