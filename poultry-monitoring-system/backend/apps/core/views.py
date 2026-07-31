"""Shared views: friendly error pages and a health-check endpoint."""
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)


def health_check(request):
    """Liveness/readiness probe used by Docker/Nginx and uptime checks."""
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pragma: no cover
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse(
        {"status": "ok" if db_ok else "degraded", "database": db_ok}, status=status
    )
