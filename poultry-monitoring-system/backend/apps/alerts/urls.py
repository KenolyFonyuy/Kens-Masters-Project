from django.urls import path

from . import views

app_name = "alerts"

urlpatterns = [
    path("", views.AlertListView.as_view(), name="alert_list"),
    path("<uuid:uid>/", views.AlertDetailView.as_view(), name="alert_detail"),
    path("<uuid:uid>/<str:action>/", views.AlertTransitionView.as_view(), name="alert_transition"),
]
