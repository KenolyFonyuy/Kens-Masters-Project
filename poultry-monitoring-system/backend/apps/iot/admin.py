from django.contrib import admin

from .models import (
    ActuatorEvent,
    DeviceConfiguration,
    DeviceHeartbeat,
    DeviceToken,
    EnvironmentalThreshold,
    IoTDevice,
    SensorReading,
    SyncRecord,
)


@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "device_id", "farm", "status", "is_online", "last_seen_at")
    list_filter = ("status", "farm", "has_camera")
    search_fields = ("name", "device_id")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("device", "label", "is_active", "last_used_at", "created_at")
    list_filter = ("is_active",)
    # Never expose the hash for copying as if it were the token.
    readonly_fields = ("key_hash", "last_used_at")


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = (
        "device", "temperature_c", "humidity_pct", "gas_risk_category",
        "quality", "server_timestamp",
    )
    list_filter = ("gas_risk_category", "quality", "device")
    date_hierarchy = "server_timestamp"


admin.site.register(DeviceConfiguration)
admin.site.register(EnvironmentalThreshold)
admin.site.register(ActuatorEvent)
admin.site.register(DeviceHeartbeat)
admin.site.register(SyncRecord)
