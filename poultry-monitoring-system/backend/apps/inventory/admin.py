from django.contrib import admin

from .models import InventoryCategory, InventoryItem, StockMovement


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "farm", "unit", "current_stock", "reorder_level", "is_active")
    list_filter = ("farm", "is_active", "category")
    search_fields = ("name", "sku")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "signed_quantity", "movement_date")
    list_filter = ("movement_type", "movement_date")
