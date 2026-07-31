from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.InventoryItemListView.as_view(), name="item_list"),
    path("add/", views.InventoryItemCreateView.as_view(), name="item_create"),
    path("<uuid:uid>/", views.InventoryItemDetailView.as_view(), name="item_detail"),
    path("<uuid:uid>/edit/", views.InventoryItemUpdateView.as_view(), name="item_update"),
    path("movements/", views.StockMovementListView.as_view(), name="movement_list"),
    path("movements/add/", views.StockMovementCreateView.as_view(), name="movement_create"),
]
