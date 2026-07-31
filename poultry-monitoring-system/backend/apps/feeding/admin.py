from django.contrib import admin

from .models import FeedType, FeedUsage


@admin.register(FeedType)
class FeedTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "phase", "protein_pct", "is_active")
    list_filter = ("phase", "is_active")


@admin.register(FeedUsage)
class FeedUsageAdmin(admin.ModelAdmin):
    list_display = ("batch", "feed_type", "record_date", "quantity_kg", "stock_applied")
    list_filter = ("record_date", "feed_type")
