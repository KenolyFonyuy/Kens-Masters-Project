from django.contrib import admin

from .models import Expense, Payment, Sale


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("farm", "category", "amount", "expense_date")
    list_filter = ("category", "expense_date", "farm")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("batch", "quantity", "unit_price", "total_amount", "status", "sale_date")
    list_filter = ("status", "sale_date", "farm")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("sale", "amount", "method", "payment_date")
    list_filter = ("method", "payment_date")
