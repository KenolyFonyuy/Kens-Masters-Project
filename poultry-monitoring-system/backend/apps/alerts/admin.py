from django.contrib import admin

from .models import Alert, AlertAction, NotificationPreference


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "alert_type", "severity", "status", "farm", "last_triggered_at")
    list_filter = ("severity", "status", "alert_type", "source")
    search_fields = ("title", "message")


admin.site.register(AlertAction)
admin.site.register(NotificationPreference)
