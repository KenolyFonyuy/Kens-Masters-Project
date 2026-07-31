from django.urls import path

from . import views

app_name = "farms"

urlpatterns = [
    path("", views.FarmListView.as_view(), name="farm_list"),
    path("add/", views.FarmCreateView.as_view(), name="farm_create"),
    path("<uuid:uid>/", views.FarmDetailView.as_view(), name="farm_detail"),
    path("<uuid:uid>/edit/", views.FarmUpdateView.as_view(), name="farm_update"),
    # Pens
    path("pens/", views.PenListView.as_view(), name="pen_list"),
    path("pens/add/", views.PenCreateView.as_view(), name="pen_create"),
    path("pens/<uuid:uid>/", views.PenDetailView.as_view(), name="pen_detail"),
    path("pens/<uuid:uid>/edit/", views.PenUpdateView.as_view(), name="pen_update"),
    # Breeds
    path("breeds/", views.BreedListView.as_view(), name="breed_list"),
    path("breeds/add/", views.BreedCreateView.as_view(), name="breed_create"),
    path("breeds/<uuid:uid>/edit/", views.BreedUpdateView.as_view(), name="breed_update"),
    # Suppliers
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/add/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path(
        "suppliers/<uuid:uid>/edit/",
        views.SupplierUpdateView.as_view(),
        name="supplier_update",
    ),
    # Customers
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/add/", views.CustomerCreateView.as_view(), name="customer_create"),
    path(
        "customers/<uuid:uid>/edit/",
        views.CustomerUpdateView.as_view(),
        name="customer_update",
    ),
]
