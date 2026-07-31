from django.contrib import admin

from .models import Attachment, AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "target_repr", "ip_address")
    list_filter = ("action",)
    search_fields = ("target_repr", "message", "object_type")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "uploaded_by", "created_at")
    search_fields = ("original_name", "description")
