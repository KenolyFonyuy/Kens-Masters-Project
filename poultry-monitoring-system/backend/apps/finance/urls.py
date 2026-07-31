from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("expenses/", views.ExpenseListView.as_view(), name="expense_list"),
    path("expenses/add/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("expenses/<uuid:uid>/edit/", views.ExpenseUpdateView.as_view(), name="expense_update"),
    path("sales/", views.SaleListView.as_view(), name="sale_list"),
    path("sales/add/", views.SaleCreateView.as_view(), name="sale_create"),
    path("sales/<uuid:uid>/", views.SaleDetailView.as_view(), name="sale_detail"),
    path("sales/<uuid:uid>/edit/", views.SaleUpdateView.as_view(), name="sale_update"),
    path("payments/add/", views.PaymentCreateView.as_view(), name="payment_create"),
]
