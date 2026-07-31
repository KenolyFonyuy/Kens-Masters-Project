from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    fieldsets = UserAdmin.fieldsets + (
        ("Poultry system", {"fields": ("uid", "role", "phone", "assigned_farms")}),
    )
    readonly_fields = ("uid",)
    filter_horizontal = ("assigned_farms", "groups", "user_permissions")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "job_title", "timezone")
