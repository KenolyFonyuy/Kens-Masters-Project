"""Standard API response helpers and a uniform DRF exception handler."""
import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.api")


def ok(data=None, status=200, **extra):
    """Standard success envelope."""
    payload = {"success": True, "data": data}
    payload.update(extra)
    return Response(payload, status=status)


def fail(message, status=400, errors=None, code=None):
    """Standard error envelope."""
    payload = {"success": False, "error": {"message": message}}
    if code:
        payload["error"]["code"] = code
    if errors is not None:
        payload["error"]["details"] = errors
    return Response(payload, status=status)


def exception_handler(exc, context):
    """Wrap DRF's default handler so every error has a consistent shape."""
    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        return fail("Internal server error.", status=500, code="server_error")

    detail = response.data
    message = "Request failed."
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        errors = None
    else:
        errors = detail
    return fail(message, status=response.status_code, errors=errors)
