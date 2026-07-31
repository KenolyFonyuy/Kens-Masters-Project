"""CSV export helper shared by report views."""
import csv

from django.http import HttpResponse


def csv_response(filename: str, header: list[str], rows):
    """Stream a list of rows as a downloadable CSV file.

    ``rows`` is any iterable of iterables aligned with ``header``.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response
