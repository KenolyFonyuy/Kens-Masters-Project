from django.contrib import admin

from .models import Breed, Customer, Farm, Pen, Supplier


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "owner", "is_active", "is_demo")
    list_filter = ("is_active", "is_demo", "region")
    search_fields = ("name", "code", "location")


@admin.register(Pen)
class PenAdmin(admin.ModelAdmin):
    list_display = ("name", "farm", "code", "capacity", "is_active")
    list_filter = ("farm", "is_active")
    search_fields = ("name", "code")


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "typical_market_age_days")
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "is_active")
    search_fields = ("name",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "customer_type", "phone", "is_active")
    list_filter = ("customer_type", "is_active")
    search_fields = ("name",)
