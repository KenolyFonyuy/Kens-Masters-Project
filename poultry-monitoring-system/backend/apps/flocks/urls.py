from django.urls import path

from . import views

app_name = "flocks"

urlpatterns = [
    path("", views.BatchListView.as_view(), name="batch_list"),
    path("add/", views.BatchCreateView.as_view(), name="batch_create"),
    path("<uuid:uid>/", views.BatchDetailView.as_view(), name="batch_detail"),
    path("<uuid:uid>/edit/", views.BatchUpdateView.as_view(), name="batch_update"),
    # Chick entries
    path("chick-entries/", views.ChickEntryListView.as_view(), name="chickentry_list"),
    path("chick-entries/add/", views.ChickEntryCreateView.as_view(), name="chickentry_create"),
    # Mortality
    path("mortality/", views.MortalityListView.as_view(), name="mortality_list"),
    path("mortality/add/", views.MortalityCreateView.as_view(), name="mortality_create"),
    # Transfers
    path("transfers/", views.TransferListView.as_view(), name="transfer_list"),
    path("transfers/add/", views.TransferCreateView.as_view(), name="transfer_create"),
    # Weights
    path("weights/", views.WeightListView.as_view(), name="weight_list"),
    path("weights/add/", views.WeightCreateView.as_view(), name="weight_create"),
    # Observations
    path("observations/", views.ObservationListView.as_view(), name="observation_list"),
    path("observations/add/", views.ObservationCreateView.as_view(), name="observation_create"),
]
