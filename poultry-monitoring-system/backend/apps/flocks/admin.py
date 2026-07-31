from django.contrib import admin

from .models import (
    Batch,
    ChickEntry,
    DailyObservation,
    MortalityRecord,
    TransferRecord,
    WeightRecord,
)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "farm", "status", "start_date", "current_quantity")
    list_filter = ("status", "farm", "is_demo")
    search_fields = ("code", "name")


@admin.register(ChickEntry)
class ChickEntryAdmin(admin.ModelAdmin):
    list_display = ("batch", "entry_date", "quantity", "supplier")
    list_filter = ("entry_date",)


@admin.register(MortalityRecord)
class MortalityAdmin(admin.ModelAdmin):
    list_display = ("batch", "record_date", "quantity", "cause")
    list_filter = ("cause", "record_date")


admin.site.register(TransferRecord)
admin.site.register(WeightRecord)
admin.site.register(DailyObservation)
