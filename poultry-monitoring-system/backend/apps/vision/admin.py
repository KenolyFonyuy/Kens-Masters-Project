from django.contrib import admin

from .models import VisionResult


@admin.register(VisionResult)
class VisionResultAdmin(admin.ModelAdmin):
    list_display = (
        "predicted_class", "confidence", "risk_category", "review_status",
        "farm", "server_timestamp",
    )
    list_filter = ("review_status", "predicted_class", "risk_category", "farm")
    search_fields = ("predicted_class", "review_notes")
    readonly_fields = ("result_uuid", "predicted_class", "confidence", "detections")
